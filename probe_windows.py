"""Read-only observations from one already-running BH6.exe. Never launches or patches it."""
import argparse
import ctypes
from ctypes import wintypes as w
import datetime
import json
import math
import os
from pathlib import Path
import struct
import time

from patch_candidate import ROOT, Rejected, digest, inspect_bytes, load_manifest
from session_probe import player_objects_snapshot, session_snapshot

CONTEXTS = ("unspecified", "main-menu", "no-mercy-lobby", "no-mercy-running",
            "mercenaries-lobby", "mercenaries-running", "other")


def snapshot(read, base, spec, disk):
    def integer(address):
        data = read(address, 4)
        return struct.unpack("<I", data)[0] if data is not None else None

    def finite_float(address):
        data = read(address, 4)
        if data is None:
            return None
        number = struct.unpack("<f", data)[0]
        return number if math.isfinite(number) else None

    candidates = spec["probe_candidates"]
    info = integer(base + candidates["game_info_root_rva"])
    mode_root = integer(base + candidates["mode_root_rva"])
    live = []
    for patch, old_rva in zip(spec["patches"], [0x60F51D, 0x60D361, 0x60D37A]):
        expected = bytes.fromhex(patch["expected_hex"])
        current = read(base + patch["rva"], len(expected))
        live.append({"name": patch["name"], "rva": hex(patch["rva"]),
                     "live_hex": current.hex() if current is not None else None,
                     "matches_original": current == expected,
                     "matches_candidate": current == bytes.fromhex(patch["replacement_hex"])})
        # Check whether the historical trainer wrote into the wrong v1.1.0 locations.
        # All three historical sites are in the file-backed .text section.
        old_offset = old_rva - 0x1000 + 0x400
        old_expected = disk[old_offset:old_offset + len(expected)]
        old_current = read(base + old_rva, len(expected))
        live[-1]["legacy_site_matches_disk"] = old_current == old_expected if old_current is not None else None

    timer = None
    stage = None
    valid_info = info is not None and 0x10000 <= info <= 0xFFF00000
    valid_mode = mode_root is not None and 0x10000 <= mode_root <= 0xFFF00000
    if valid_info:
        timer = finite_float(info + candidates["timer_relative_to_game_info"])
        stage = integer(info + candidates["stage_field_offset"])
    mode = integer(mode_root + 0xAC) if valid_mode else None
    native_timer = None
    elapsed = None
    timer_state = None
    same_address = None
    if valid_mode:
        # This displacement is independently supported by the current game's
        # float subtraction/addition paths. Still observations, never a write.
        native_timer = finite_float(mode_root + candidates["native_timer_field_offset"])
        elapsed = finite_float(mode_root + candidates["native_elapsed_field_offset"])
        timer_state = integer(mode_root + candidates["native_timer_state_offset"])
        if valid_info:
            same_address = (info + candidates["timer_relative_to_game_info"] ==
                            mode_root + candidates["native_timer_field_offset"])
    return {"time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "game_info_root": hex(info) if info else None,
            "mode_root": hex(mode_root) if mode_root else None,
            "mode_field_candidate": mode, "stage_field_candidate": stage,
            "timer_field_candidate": timer, "native_sites": live,
            "native_timer_field_candidate": native_timer,
            "native_elapsed_field_candidate": elapsed,
            "native_timer_state_candidate": timer_state,
            "timer_candidates_same_address": same_address,
            "session": session_snapshot(read, base, candidates["mode_root_rva"]),
            "player_objects": player_objects_snapshot(read, base, candidates["player_manager_root_rva"]),
            "status": "OBSERVATIONS ONLY; NOT A GAMEPLAY TEST"}


class WindowsReader:
    def __init__(self, proc_id):
        if os.name != "nt":
            raise Rejected("Live observations require Windows; no process was opened.")
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        api = self.api
        api.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        api.OpenProcess.restype = w.HANDLE
        api.CloseHandle.argtypes = [w.HANDLE]
        api.CloseHandle.restype = w.BOOL
        api.ReadProcessMemory.argtypes = [w.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                         ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        api.ReadProcessMemory.restype = w.BOOL
        api.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]
        api.QueryFullProcessImageNameW.restype = w.BOOL
        api.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
        api.CreateToolhelp32Snapshot.restype = w.HANDLE
        # PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION. No write, injection,
        # thread creation, suspension, or memory-protection rights are requested.
        self.handle = api.OpenProcess(0x1010, False, proc_id)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        self.proc_id = proc_id

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None

    def image_path(self):
        buffer = ctypes.create_unicode_buffer(32768)
        size = w.DWORD(len(buffer))
        if not self.api.QueryFullProcessImageNameW(self.handle, 0, buffer, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        return Path(buffer.value)

    def module(self):
        class Entry(ctypes.Structure):
            _fields_ = [("dwSize", w.DWORD), ("th32ModuleID", w.DWORD),
                        ("th32ProcessID", w.DWORD), ("GlblcntUsage", w.DWORD),
                        ("ProccntUsage", w.DWORD), ("modBaseAddr", ctypes.c_void_p),
                        ("modBaseSize", w.DWORD), ("hModule", w.HMODULE),
                        ("szModule", w.WCHAR * 256), ("szExePath", w.WCHAR * 260)]
        api = self.api
        for name in ["Module32FirstW", "Module32NextW"]:
            getattr(api, name).argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
            getattr(api, name).restype = w.BOOL
        handle = api.CreateToolhelp32Snapshot(0x8 | 0x10, self.proc_id)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            entry = Entry()
            entry.dwSize = ctypes.sizeof(Entry)
            ok = api.Module32FirstW(handle, ctypes.byref(entry))
            while ok:
                if entry.szModule.lower() == "bh6.exe":
                    return entry.modBaseAddr, entry.modBaseSize
                ok = api.Module32NextW(handle, ctypes.byref(entry))
            raise Rejected("BH6.exe module was not found in the selected process.")
        finally:
            api.CloseHandle(handle)

    def read(self, address, size):
        if size < 1 or size > 4096:
            raise Rejected("Unexpected observation size.")
        buffer = ctypes.create_string_buffer(size)
        copied = ctypes.c_size_t()
        ok = self.api.ReadProcessMemory(self.handle, ctypes.c_void_p(address), buffer,
                                        size, ctypes.byref(copied))
        return buffer.raw if ok and copied.value == size else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", required=True, type=int)
    parser.add_argument("--samples", type=int, default=6)
    parser.add_argument("--interval", type=float, default=1)
    parser.add_argument("--context", choices=CONTEXTS, default="unspecified",
                        help="Your screen/mode label; not an automatically verified game mode.")
    parser.add_argument("--delay", type=float, default=0,
                        help="Seconds to return focus to the game before sampling (0-60).")
    args = parser.parse_args()
    if not 1 <= args.samples <= 60 or not 0.1 <= args.interval <= 5 or not 0 <= args.delay <= 60:
        parser.error("Use 1-60 samples, a 0.1-5 second interval, and a 0-60 second delay.")
    reader = None
    try:
        spec = load_manifest()
        reader = WindowsReader(args.pid)
        path = reader.image_path()
        if path.name.lower() != "bh6.exe":
            raise Rejected("Selected process is not BH6.exe.")
        disk = path.read_bytes()
        inspect_bytes(disk, spec)
        base, size = reader.module()
        if size != 21671936:
            raise Rejected("Unexpected module size for the supplied build.")
        header = reader.read(base, 0x40)
        if header is None or header[:2] != b"MZ":
            raise Rejected("Live image header is unreadable or unexpected.")
        print(f"Read-only capture: {args.context}; {args.samples} samples.", flush=True)
        if args.delay:
            print(f"Sampling starts in {args.delay:g} seconds; return to the chosen game screen.", flush=True)
            time.sleep(args.delay)
        observations = []
        for i in range(args.samples):
            observations.append(snapshot(reader.read, base, spec, disk))
            if i + 1 < args.samples:
                time.sleep(args.interval)
        report = {"schema": 3, "access": "READ ONLY", "gameplay_test": False,
                  "context_user_reported": args.context,
                  "exe_sha256": digest(disk), "module_base": hex(base),
                  "module_size": size, "samples": observations}
        directory = ROOT / "private"
        directory.mkdir(exist_ok=True)
        if not directory.resolve().is_relative_to(ROOT):
            raise Rejected("Output escapes the project workspace.")
        name = "probe-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
        with (directory / name).open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
        print(f"Read-only report saved: private/{name}")
    except (OSError, Rejected, ValueError) as exc:
        parser.exit(1, f"Observation stopped: {exc}\n")
    finally:
        if reader is not None:
            reader.close()


if __name__ == "__main__":
    main()
