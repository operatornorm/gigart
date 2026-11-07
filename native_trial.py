"""Experimental three-site memory trial on an isolated test copy; inspect by default."""
import argparse
from contextlib import contextmanager
import ctypes
from ctypes import wintypes as w
import datetime
import json
import os
from pathlib import Path

from patch_candidate import ROOT, Rejected, candidate_bytes, load_manifest
from probe_windows import WindowsReader, snapshot


def mutation_plan(read, base, disk, spec, restore=False):
    # Validates the input AND pinned output hash before trusting replacements.
    candidate_bytes(disk, spec)
    if base != spec["image_base"]:
        raise Rejected("Relocated modules are unsupported by this experiment.")
    plans = []
    for patch in spec["patches"]:
        original = bytes.fromhex(patch["expected_hex"])
        replacement = bytes.fromhex(patch["replacement_hex"])
        before, after = (replacement, original) if restore else (original, replacement)
        context = bytearray.fromhex(patch["context_hex"])
        relative = patch["file_offset"] - patch["context_offset"]
        if relative < 0 or relative + len(before) > len(context):
            raise Rejected("Patch is not covered by its context guard.")
        context[relative:relative + len(before)] = before
        context_address = base + patch["rva"] - relative
        if read(context_address, len(context)) != bytes(context):
            raise Rejected(f"Live code/context mismatch: {patch['name']}. No writes made.")
        address = base + patch["rva"]
        if read(address, len(before)) != before:
            raise Rejected(f"Live instructions changed: {patch['name']}. No writes made.")
        plans.append((address, before, after))
    # The old trainer must not have modified its historical targets either.
    for patch, old_rva in zip(spec["patches"], (0x60F51D, 0x60D361, 0x60D37A)):
        size = len(bytes.fromhex(patch["expected_hex"]))
        offset = old_rva - 0x1000 + 0x400
        expected = disk[offset:offset + size]
        if len(expected) != size or read(base + old_rva, size) != expected:
            raise Rejected("Historical trainer target differs from disk. Restart with trainer off.")
    return plans


def require_idle_menu(observation, manager_absent=False):
    session, objects = observation["session"], observation["player_objects"]
    if observation["stage_field_candidate"] != 1102:
        raise Rejected("Not the observed menu scene. Return to the main menu first.")
    if session["root_stable"] is not True or (not manager_absent and objects["root_stable"] is not True):
        raise Rejected("Unstable or unreadable roots; no mutation allowed.")
    if not manager_absent and objects["entry_present"] != [False]*8:
        raise Rejected("Player objects exist or are unreadable. No mutation allowed.")
    fields = session["fields"]
    if fields is None or fields.get("session_type_candidate") not in (0, 4):
        raise Rejected("A host/join session may be active. Exit the lobby; restart if needed.")
    slots = session["slots"]
    if slots is None or len(slots) != 8 or any(
            row.get("slot_state") != 0 for row in slots[1:]):
        raise Rejected("Other slots are occupied or unreadable. No mutation allowed.")


def apply_transaction(read, write, plans):
    """Caller must hold the game's process suspension for the entire operation."""
    # Recheck every span before the first write, including guard-to-write drift.
    if any(read(address, len(before)) != before for address, before, _ in plans):
        raise Rejected("Instructions changed before transaction. No writes made.")
    attempted = []
    try:
        for address, before, after in plans:
            attempted.append((address, before))  # Include partially failed writes.
            write(address, after)
            if read(address, len(after)) != after:
                raise Rejected("Candidate write did not read back correctly.")
        if any(read(a, len(after)) != after for a, _, after in plans):
            raise Rejected("Final transaction verification failed.")
    except BaseException as exc:
        errors = []
        for address, before in reversed(attempted):
            try:
                write(address, before)
                if read(address, len(before)) != before:
                    raise Rejected("Rollback readback mismatch")
            except BaseException as rollback_error:
                errors.append(f"{hex(address)}: {rollback_error}")
        if errors:
            raise Rejected("WRITE FAILED; ROLLBACK INCOMPLETE. Close the test game. "
                           + "; ".join(errors)) from exc
        raise Rejected(f"Write failed; previous bytes restored: {exc}") from exc


def lobby_assessment(observation):
    session = observation["session"]
    fields = session["fields"]
    slots = session["slots"]
    if (session["root_stable"] is not True or fields is None or slots is None
            or len(slots) != 8):
        return "UNKNOWN: session fields unavailable"
    sites = observation["native_sites"]
    patched = len(sites) == 3 and all(site["matches_candidate"] and site["legacy_site_matches_disk"]
                                    for site in sites)
    kinds = [row["slot_kind"] for row in slots]
    states = [row["slot_state"] for row in slots]
    randomized = [row["randomized_slot"] for row in slots[:6]]
    objects = observation["player_objects"]
    if (patched and objects["root_stable"] is True and objects["entry_present"] == [False]*8
            and fields["session_type_candidate"] == 1
            and fields["create_capacity_candidate"] == 6
            and kinds[0] == 3 and states[0] == 1
            and all(k in (1, 2) for k in kinds[1:6])
            and states[1:] == [0]*7 and kinds[6:] == [0, 0]
            and None not in randomized and sorted(randomized) == list(range(6))):
        return "SIX-SLOT CONFIGURATION OBSERVED; NETWORK/NO MERCY/GAMEPLAY NOT VALIDATED"
    return "EXPECTED SIX-SLOT CONFIGURATION NOT OBSERVED; DO NOT START A ROUND"


class WindowsTrialProcess(WindowsReader):
    """Separate opt-in writer; the ordinary collector keeps read-only rights."""
    def __init__(self, proc_id):
        super().__init__(proc_id)
        try:
            # VM operation/read/write + limited query + suspend/resume.
            handle = self.api.OpenProcess(0x1838, False, proc_id)
            if not handle:
                raise ctypes.WinError(ctypes.get_last_error())
            self.api.CloseHandle(self.handle)
            self.handle = handle
            self.nt = ctypes.WinDLL("ntdll")
            for name in ("NtSuspendProcess", "NtResumeProcess"):
                function = getattr(self.nt, name)
                function.argtypes = [w.HANDLE]
                function.restype = ctypes.c_int32
            self.api.VirtualProtectEx.argtypes = [w.HANDLE, ctypes.c_void_p,
                                                  ctypes.c_size_t, w.DWORD, ctypes.POINTER(w.DWORD)]
            self.api.VirtualProtectEx.restype = w.BOOL
            self.api.WriteProcessMemory.argtypes = [w.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                                    ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
            self.api.WriteProcessMemory.restype = w.BOOL
            self.api.FlushInstructionCache.argtypes = [w.HANDLE, ctypes.c_void_p, ctypes.c_size_t]
            self.api.FlushInstructionCache.restype = w.BOOL
            self.is_suspended = False
            self.protection_failed = False
        except BaseException:
            self.close()
            raise

    @contextmanager
    def suspended(self):
        status = self.nt.NtSuspendProcess(self.handle)
        if status < 0:
            raise Rejected(f"Process suspension failed (NTSTATUS 0x{status & 0xFFFFFFFF:08x}).")
        self.is_suspended = True
        try:
            yield
        finally:
            status = self.nt.NtResumeProcess(self.handle)
            self.is_suspended = False
            if status < 0:
                raise Rejected("Could not resume the test process; close it with Task Manager. "
                               f"NTSTATUS 0x{status & 0xFFFFFFFF:08x}.")

    def write_code(self, address, value):
        if not self.is_suspended:
            raise Rejected("Refusing a code write while game threads can execute.")
        old = w.DWORD()
        if not self.api.VirtualProtectEx(self.handle, address, len(value), 0x40, ctypes.byref(old)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            data = ctypes.create_string_buffer(value)
            copied = ctypes.c_size_t()
            if not self.api.WriteProcessMemory(self.handle, address, data, len(value), ctypes.byref(copied)):
                raise ctypes.WinError(ctypes.get_last_error())
            if copied.value != len(value):
                raise Rejected("Partial process-memory write.")
            if not self.api.FlushInstructionCache(self.handle, address, len(value)):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            ignored = w.DWORD()
            if not self.api.VirtualProtectEx(self.handle, address, len(value), old.value, ctypes.byref(ignored)):
                self.protection_failed = True
                raise Rejected("Failed to restore memory protection. Close the test game.")
        if self.protection_failed:
            raise Rejected("An earlier protection restore failed; close the test game.")


def validate_process(reader, spec, test_executable=None):
    path = reader.image_path()
    if path.name.lower() != "bh6.exe":
        raise Rejected("Selected process is not BH6.exe.")
    if test_executable is not None and os.path.normcase(str(path.resolve())) != os.path.normcase(
            str(test_executable.resolve(strict=True))):
        raise Rejected("Process is not running from the specified isolated test executable.")
    disk = path.read_bytes()
    candidate_bytes(disk, spec)
    base, size = reader.module()
    if base != spec["image_base"] or size != 21671936:
        raise Rejected("Unexpected module base/size for the supported build.")
    header = reader.read(base, 0x40)
    if header is None or header[:2] != b"MZ":
        raise Rejected("Unexpected live image header.")
    return base, disk


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true", help="Apply the experimental native candidate in memory.")
    action.add_argument("--restore", action="store_true", help="Restore all three original instruction spans.")
    parser.add_argument("--test-exe", type=Path,
                        help="Required for writes: exact BH6.exe path in your isolated test copy.")
    args = parser.parse_args()
    changing = args.apply or args.restore
    if changing and args.test_exe is None:
        parser.error("Writes require --test-exe pointing to an isolated test copy, not the original install.")
    reader = None
    mutation_completed = False
    try:
        # Prepare private output before opening or modifying a process.
        directory = ROOT / "private"
        directory.mkdir(exist_ok=True)
        if not directory.resolve().is_relative_to(ROOT):
            raise Rejected("Audit output escapes the kit workspace.")
        spec = load_manifest()
        reader = WindowsTrialProcess(args.pid) if changing else WindowsReader(args.pid)
        base, disk = validate_process(reader, spec, args.test_exe if changing else None)
        report = {"schema": 1, "action": "restore" if args.restore else "apply" if args.apply else "inspect",
                  "exe_sha256": spec["input_sha256"], "gameplay_validated": False}
        if changing:
            # Revalidate identity/state/guards after suspending every game thread.
            # The suspension is held only during validation, writes and rollback.
            with reader.suspended():
                base, disk = validate_process(reader, spec, args.test_exe)
                before = snapshot(reader.read, base, spec, disk)
                # A not-yet-created sPlayer manager is distinct from a failed
                # read. This direct zero-root check is made while suspended.
                manager_absent = reader.read(base + spec["probe_candidates"]["player_manager_root_rva"], 4) == b"\0"*4
                require_idle_menu(before, manager_absent=manager_absent)
                report["player_manager_absent_at_menu"] = manager_absent
                plans = mutation_plan(reader.read, base, disk, spec, restore=args.restore)
                apply_transaction(reader.read, reader.write_code, plans)
                mutation_completed = True
                report["before"] = before
                report["after"] = snapshot(reader.read, base, spec, disk)
        else:
            report["observation"] = snapshot(reader.read, base, spec, disk)
            report["lobby_assessment"] = lobby_assessment(report["observation"])
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        name = f"trial-{report['action']}-{stamp}.json"
        with (directory / name).open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
        print(f"Private report: private/{name}")
        if changing:
            print("Native candidate applied." if args.apply else "Original code restored.")
            print("No game file, timer, mode or save was written. Windows trial remains experimental.")
        else:
            print(report["lobby_assessment"])
    except (OSError, Rejected, ValueError, AttributeError) as exc:
        suffix = (" The code transaction completed before this later error; close the test game "
                  "to discard the in-memory changes." if mutation_completed else "")
        parser.exit(1, f"Trial stopped: {exc}{suffix}\n")
    finally:
        if reader is not None:
            reader.close()


if __name__ == "__main__":
    main()
