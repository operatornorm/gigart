"""Exercise the Windows writer against an owned synthetic process, never RE6."""
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import time

from native_trial import WindowsTrialProcess, apply_transaction
from patch_candidate import Rejected


def wait_until(function, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        result = function()
        if result:
            return result
        time.sleep(0.02)
    raise Rejected("Owned backend fixture timed out.")


def protection(reader, address):
    class Information(ctypes.Structure):
        _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                    ("AllocationProtect", w.DWORD), ("RegionSize", ctypes.c_size_t),
                    ("State", w.DWORD), ("Protect", w.DWORD), ("Type", w.DWORD)]
    function = reader.api.VirtualQueryEx
    function.argtypes = [w.HANDLE, ctypes.c_void_p, ctypes.POINTER(Information), ctypes.c_size_t]
    function.restype = ctypes.c_size_t
    info = Information()
    # VirtualQueryEx needs QUERY_INFORMATION. The actual writer intentionally
    # has only QUERY_LIMITED_INFORMATION; do not alter its tested access mask.
    query = reader.api.OpenProcess(0x400, False, reader.proc_id)
    if not query:
        raise Rejected("Cannot open an information-only handle to the owned fixture.")
    try:
        size = function(query, address, ctypes.byref(info), ctypes.sizeof(info))
        if size != ctypes.sizeof(info):
            raise Rejected(f"Cannot inspect fixture memory protection: size {size}, "
                           f"WinError {ctypes.get_last_error()}.")
    finally:
        reader.api.CloseHandle(query)
    return info.Protect


def run_check(fixture):
    fixture = Path(fixture).resolve(strict=True)
    if fixture.name.casefold() != "re6backendfixture.exe":
        raise Rejected("Backend check only launches RE6BackendFixture.exe.")
    original = bytes(range(64))
    replacement = bytes(reversed(original))
    with tempfile.TemporaryDirectory(prefix="re6-backend-check-") as directory:
        directory = Path(directory)
        child = subprocess.Popen([str(fixture), str(directory)])
        reader = None
        try:
            ready = directory / "ready.json"
            wait_until(ready.is_file)
            state = json.loads(ready.read_text())
            if state["pid"] != child.pid or state["pointer_bits"] != 32:
                raise Rejected("Unexpected backend fixture identity or architecture.")
            reader = WindowsTrialProcess(child.pid)
            if reader.image_path().resolve() != fixture:
                raise Rejected("The opened process is not the owned fixture.")
            address, counter = state["address"], state["counter"]

            def tick():
                data = reader.read(counter, 4)
                if data is None:
                    raise Rejected("Fixture counter is unreadable.")
                return struct.unpack("<I", data)[0]

            def require(condition, message):
                if not condition:
                    raise Rejected(message)

            require(reader.read(address, 64) == original, "Fixture original bytes differ.")
            require(protection(reader, address) == 2, "Fixture page is not read-only.")
            before = tick()
            wait_until(lambda: tick() != before)
            with reader.suspended():
                before = tick()
                time.sleep(0.08)
                require(tick() == before, "Fixture kept running during suspension.")
                apply_transaction(reader.read, reader.write_code, [(address, original, replacement)])
                require(protection(reader, address) == 2, "Page protection was not restored after apply.")
            wait_until(lambda: tick() != before)
            require(reader.read(address, 64) == replacement, "Fixture apply readback failed.")
            with reader.suspended():
                apply_transaction(reader.read, reader.write_code, [(address, replacement, original)])
                require(protection(reader, address) == 2, "Page protection was not restored after undo.")
                before = tick()
            wait_until(lambda: tick() != before)
            require(reader.read(address, 64) == original, "Fixture original bytes were not restored.")
            return {"success": True, "target": "owned 32-bit synthetic fixture; no game access",
                    "helper_pointer_bits": ctypes.sizeof(ctypes.c_void_p) * 8,
                    "read_only_page_write": True, "apply_restore_readback": True,
                    "page_protection_restored": True, "suspend_and_resume_observed": True}
        finally:
            if reader is not None:
                reader.close()
            (directory / "stop").touch()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
