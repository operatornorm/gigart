"""Portable launcher for the unchanged, tested RE6 Mercenaries memory patch."""
import argparse
import ctypes
from ctypes import wintypes as w
import datetime
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys

from native_trial import (WindowsTrialProcess, apply_transaction, mutation_plan,
                          require_idle_menu, validate_process)
from patch_candidate import ROOT, Rejected, load_manifest
from probe_windows import WindowsReader, snapshot

VERSION = "0.2.0"
APP_ID = "221040"


def parse_vdf(text):
    """Read Valve KeyValues, including escaped paths and // comments."""
    if len(text) > 1024 * 1024:
        raise Rejected("Steam configuration is unexpectedly large.")
    lexer = re.compile(r'\s+|//[^\r\n]*|"(?:\\.|[^"\\])*"|[{}]|[^\s{}"]+')
    tokens = []
    position = 0
    for match in lexer.finditer(text):
        if match.start() != position:
            raise Rejected("Malformed Steam configuration.")
        position = match.end()
        token = match.group()
        if token.isspace() or token.startswith("//"):
            continue
        if token.startswith('"'):
            token = re.sub(r'\\([\\"])', r'\1', token[1:-1])
            tokens.append(("string", token))
        else:
            tokens.append((token if token in ("{", "}") else "string", token))
    if position != len(text):
        raise Rejected("Malformed Steam configuration.")
    cursor = 0

    def object_value(nested=False, depth=0):
        nonlocal cursor
        if depth > 32:
            raise Rejected("Steam configuration is nested too deeply.")
        result = {}
        while cursor < len(tokens):
            kind, key = tokens[cursor]
            cursor += 1
            if kind == "}" and nested:
                return result
            if kind != "string" or cursor >= len(tokens):
                raise Rejected("Malformed Steam key/value pair.")
            key = key.casefold()
            if key in result:
                raise Rejected("Duplicate Steam configuration key.")
            kind, value = tokens[cursor]
            cursor += 1
            if kind == "{":
                value = object_value(True, depth + 1)
            elif kind != "string":
                raise Rejected("Malformed Steam configuration value.")
            result[key] = value
        if nested:
            raise Rejected("Unclosed Steam configuration object.")
        return result

    return object_value()


def read_vdf(path):
    with path.open("r", encoding="utf-8-sig") as stream:
        return parse_vdf(stream.read(1024 * 1024 + 1))


def steam_roots():
    if os.name != "nt":
        raise Rejected("This launcher runs on Windows.")
    import winreg
    roots = []
    locations = (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
    )
    for hive, key, value in locations:
        for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            try:
                with winreg.OpenKey(hive, key, 0, winreg.KEY_READ | view) as handle:
                    root, kind = winreg.QueryValueEx(handle, value)
                    if kind in (winreg.REG_SZ, winreg.REG_EXPAND_SZ) and root:
                        roots.append(Path(os.path.expandvars(root)))
            except OSError:
                continue
    return roots


def path_key(path):
    return os.path.normcase(str(path.resolve()))


def discover_installs(roots):
    """Only registered Steam app 221040 installations qualify."""
    libraries = {path_key(Path(root)): Path(root) for root in roots}
    for root in list(libraries.values()):
        config = root / "steamapps" / "libraryfolders.vdf"
        if not config.is_file():
            continue
        folders = read_vdf(config).get("libraryfolders")
        if not isinstance(folders, dict):
            raise Rejected("Steam library configuration has no libraryfolders object.")
        for index, entry in folders.items():
            if not index.isdigit():
                continue
            path = entry.get("path") if isinstance(entry, dict) else entry
            if isinstance(path, str) and path:
                library = Path(path)
                libraries[path_key(library)] = library
    installs = {}
    for library in libraries.values():
        manifest = library / "steamapps" / f"appmanifest_{APP_ID}.acf"
        if not manifest.is_file():
            continue
        app = read_vdf(manifest).get("appstate")
        if not isinstance(app, dict) or app.get("appid") != APP_ID:
            raise Rejected("RE6 Steam manifest has an unexpected app ID.")
        name = app.get("installdir")
        if (not isinstance(name, str) or not name or name in (".", "..")
                or any(c in name for c in '/\\:') or PureWindowsPath(name).drive):
            raise Rejected("RE6 Steam manifest has an unsafe installation folder.")
        common = (library / "steamapps" / "common").resolve()
        executable = common / name / "BH6.exe"
        if not executable.resolve().is_relative_to(common):
            raise Rejected("RE6 installation resolves outside its Steam library.")
        if executable.is_file():
            installs[path_key(executable)] = executable.resolve()
    return list(installs.values())


def choose_pid(processes):
    matches = [pid for pid, name in processes if name.casefold() == "bh6.exe"]
    if not matches:
        raise Rejected("Start Resident Evil 6 from Steam, reach the main menu, then click Refresh.")
    if len(matches) != 1:
        raise Rejected("More than one BH6.exe is running. Close the extra game instance and refresh.")
    return matches[0]


def running_processes():
    if os.name != "nt":
        raise Rejected("This launcher runs on Windows.")

    class ProcessEntry(ctypes.Structure):
        _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD),
                    ("th32ProcessID", w.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", w.DWORD), ("cntThreads", w.DWORD),
                    ("th32ParentProcessID", w.DWORD), ("pcPriClassBase", w.LONG),
                    ("dwFlags", w.DWORD), ("szExeFile", w.WCHAR * 260)]

    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
    api.CreateToolhelp32Snapshot.restype = w.HANDLE
    for name in ("Process32FirstW", "Process32NextW"):
        function = getattr(api, name)
        function.argtypes = [w.HANDLE, ctypes.POINTER(ProcessEntry)]
        function.restype = w.BOOL
    api.CloseHandle.argtypes = [w.HANDLE]
    api.CloseHandle.restype = w.BOOL
    handle = api.CreateToolhelp32Snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(entry)
        processes = []
        ok = api.Process32FirstW(handle, ctypes.byref(entry))
        while ok:
            processes.append((entry.th32ProcessID, entry.szExeFile))
            ok = api.Process32NextW(handle, ctypes.byref(entry))
        if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
            raise ctypes.WinError(ctypes.get_last_error())
        return processes
    finally:
        api.CloseHandle(handle)


def pinned_manifest():
    spec = load_manifest()
    tested = json.loads((ROOT / "docs" / "tested-build.json").read_text(encoding="utf-8"))
    if any(spec.get(key) != value for key, value in tested["patch_specification"].items()):
        raise Rejected("Patch differs from the frozen three-player build. Re-download the release.")
    return spec


def validate_steam_process(reader, spec, installs):
    actual = reader.image_path()
    if path_key(actual) not in {path_key(path) for path in installs}:
        raise Rejected("The running game is not a registered RE6 Steam installation. "
                       "Close the test copy and launch RE6 through Steam.")
    return validate_process(reader, spec)


def code_state(reader, base, disk, spec):
    # Check whole contexts and historical targets, not just replacement spans.
    for state, restore in (("original", False), ("applied", True)):
        try:
            mutation_plan(reader.read, base, disk, spec, restore=restore)
            return state
        except Rejected:
            continue
    raise Rejected("Live code differs from both supported states. Restart RE6 with other trainers off.")


def menu_check(reader, base, spec, observation):
    absent = reader.read(base + spec["probe_candidates"]["player_manager_root_rva"], 4) == b"\0" * 4
    require_idle_menu(observation, manager_absent=absent)


def audit_directory():
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise Rejected("Windows LOCALAPPDATA is unavailable; cannot prepare a local patch log.")
    directory = Path(local) / "RE6MercenariesPatch" / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def run_action(action="inspect"):
    if action not in ("inspect", "apply", "restore"):
        raise Rejected("Unknown patch action.")
    spec = pinned_manifest()
    installs = discover_installs(steam_roots())
    if not installs:
        raise Rejected("No installed Steam copy of RE6 (app 221040) was found.")
    pid = choose_pid(running_processes())
    changing = action != "inspect"
    # Reserve an audit file before opening the game for writes.
    audit = None
    if changing:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        audit = (audit_directory() / f"{action}-{stamp}.json").open("x", encoding="utf-8")
    reader = None
    completed = False
    report = {"launcher_version": VERSION, "action": action,
              "tested_source": "v0.1.0-tested", "exe_sha256": spec["input_sha256"]}
    try:
        reader = WindowsTrialProcess(pid) if changing else WindowsReader(pid)
        base, disk = validate_steam_process(reader, spec, installs)
        if changing:
            # All original writer, pause, state, guard and rollback logic is reused.
            with reader.suspended():
                base, disk = validate_steam_process(reader, spec, installs)
                before = snapshot(reader.read, base, spec, disk)
                menu_check(reader, base, spec, before)
                plans = mutation_plan(reader.read, base, disk, spec, restore=action == "restore")
                apply_transaction(reader.read, reader.write_code, plans)
                completed = True
                report["before"] = before
                report["after"] = snapshot(reader.read, base, spec, disk)
            state = "applied" if action == "apply" else "original"
            can_change, reason = True, "Ready at the main menu."
        else:
            state = code_state(reader, base, disk, spec)
            observation = snapshot(reader.read, base, spec, disk)
            try:
                menu_check(reader, base, spec, observation)
                can_change, reason = True, "Ready at the main menu."
            except Rejected as exc:
                can_change, reason = False, str(exc)
        report.update(state=state, can_change=can_change, reason=reason)
        return report
    except Exception as exc:
        report["error"] = str(exc)
        report["transaction_completed"] = completed
        if completed:
            raise Rejected(f"Code transaction completed before a later error: {exc} "
                           "Close RE6 to discard memory changes.") from exc
        raise
    finally:
        if reader is not None:
            reader.close()
        if audit is not None:
            try:
                json.dump(report, audit, indent=2, allow_nan=False)
            except Exception as exc:
                suffix = " The code transaction completed; close RE6 to discard it." if completed else ""
                raise Rejected(f"Could not save the local patch log: {exc}.{suffix}") from exc
            finally:
                audit.close()


def gui(smoke_test=False):
    import tkinter as tk
    from tkinter import ttk
    root = tk.Tk()
    root.title(f"RE6 Mercenaries Patch {VERSION}")
    root.geometry("660x480")
    root.minsize(640, 460)
    frame = ttk.Frame(root, padding=22)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="RE6 Mercenaries Patch", font=("Segoe UI", 18, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Three-player play reported in standard Mercenaries and No Mercy.\n"
              "Uses the exact tested patch. Four or more players remain unverified.",
              wraplength=600).pack(anchor="w", pady=(8, 14))
    ttk.Label(frame, text="1. Start RE6 normally through Steam; stay at the main menu.\n"
              "2. Turn Fluffy's trainer off, then click Refresh and Apply.\n"
              "3. Host a fresh Mercenaries lobby and invite your friends.",
              wraplength=600).pack(anchor="w")
    status = tk.StringVar(value="Click Refresh after RE6 reaches its main menu.")
    ttk.Label(frame, textvariable=status, wraplength=600).pack(anchor="w", pady=18)
    controls = ttk.Frame(frame)
    controls.pack(anchor="w")

    def perform(action):
        for button in buttons:
            button.configure(state="disabled")
        status.set("Checking RE6…" if action == "inspect" else "Updating RE6 memory…")
        root.update_idletasks()
        try:
            result = run_action(action)
            active = result["state"] == "applied"
            status.set(("Patch applied. Host a fresh lobby." if result["can_change"] else
                        "Patch applied. Return to the main menu to restore.") if active else
                       "Original game code. " + result["reason"])
            if result["can_change"]:
                (restore if active else apply).configure(state="normal")
        except (OSError, ValueError, AttributeError) as exc:
            status.set(str(exc))
        finally:
            refresh.configure(state="normal")

    refresh = ttk.Button(controls, text="Refresh", command=lambda: perform("inspect"))
    apply = ttk.Button(controls, text="Apply", state="disabled", command=lambda: perform("apply"))
    restore = ttk.Button(controls, text="Restore", state="disabled", command=lambda: perform("restore"))
    buttons = (refresh, apply, restore)
    for button in buttons:
        button.pack(side="left", padx=(0, 10))
    ttk.Label(frame, text="Apply once per game launch. Closing RE6 restores original code.\n"
              "Return to the main menu before Restore. No game files or saves are edited.",
              wraplength=600).pack(anchor="w", pady=(16, 0))
    if smoke_test:
        root.update()
        root.destroy()
    else:
        root.mainloop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    for action in ("inspect", "apply", "restore", "self-test"):
        actions.add_argument(f"--{action}", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        pinned_manifest()
        running_processes()  # Enumerate only; never open or write a game process.
        gui(smoke_test=True)
        return
    if args.inspect or args.apply or args.restore:
        try:
            result = run_action("apply" if args.apply else "restore" if args.restore else "inspect")
            if sys.stdout is not None:
                print(json.dumps(result, indent=2, allow_nan=False))
        except (OSError, ValueError, AttributeError) as exc:
            parser.exit(1, f"Stopped: {exc}\n")
    else:
        gui()


if __name__ == "__main__":
    main()
