"""Discover a 32-bit Proton image through its WoW64 PEB, not Toolhelp modules."""
import ctypes
from ctypes import wintypes as w
import struct

from native_trial import WindowsTrialProcess
from patch_candidate import Rejected
from probe_windows import WindowsReader


def image_from_wow64_peb(read, query_peb):
    """Read the selected process's image headers with bounded, rechecked reads."""
    def exact(address, size, label):
        value = read(address, size)
        if value is None or len(value) != size:
            raise Rejected(f"Cannot read Proton {label} at {hex(address)}.")
        return value

    def image_base(peb):
        if peb is None or not 0x10000 <= peb <= 0xFFFFF000:
            raise Rejected("No valid 32-bit WoW64 PEB was returned for RE6.")
        return struct.unpack("<I", exact(peb + 8, 4, "32-bit image-base pointer"))[0]

    peb = query_peb()
    base = image_base(peb)
    if not 0x10000 <= base <= 0xFFFF0000:
        raise Rejected("Invalid Proton image-base pointer.")
    dos = exact(base, 64, "DOS image header")
    if dos[:2] != b"MZ":
        raise Rejected("The Proton process image has no MZ header.")
    pe_offset = struct.unpack_from("<I", dos, 0x3C)[0]
    if not 0x40 <= pe_offset <= 0x1000 or base + pe_offset + 88 > 0x100000000:
        raise Rejected("Invalid Proton PE-header offset.")
    pe = exact(base + pe_offset, 88, "PE32 image header")
    machine, sections = struct.unpack_from("<HH", pe, 4)
    optional_size = struct.unpack_from("<H", pe, 20)[0]
    magic = struct.unpack_from("<H", pe, 24)[0]
    if (pe[:4] != b"PE\0\0" or machine != 0x14C or magic != 0x10B
            or not 1 <= sections <= 96 or optional_size < 0x60):
        raise Rejected("The Proton process image is not a valid x86 PE32 image.")
    size = struct.unpack_from("<I", pe, 80)[0]
    if (size < pe_offset + 24 + optional_size or size % 0x1000
            or base + size > 0x100000000):
        raise Rejected("Invalid Proton image size.")
    if query_peb() != peb or image_base(peb) != base:
        raise Rejected("Proton image/PEB changed during validation.")
    return base, size, {"method": "ProcessWow64Information / PEB32.ImageBaseAddress",
                        "peb32": hex(peb), "image_base": hex(base), "image_size": size,
                        "pe_machine": machine, "pe_preferred_base": hex(struct.unpack_from("<I", pe, 52)[0]),
                        "root_stable": True}


class ProtonImageQuery:
    def image_path(self):
        self.validation_stage = "query_process_image_path"
        path = super().image_path()
        self.validation_stage = "read_and_validate_disk_executable"
        return path

    def _wow64_peb(self):
        nt = ctypes.WinDLL("ntdll")
        function = nt.NtQueryInformationProcess
        function.argtypes = [w.HANDLE, w.ULONG, ctypes.c_void_p, w.ULONG, ctypes.POINTER(w.ULONG)]
        function.restype = ctypes.c_int32
        # Query-only handle: preserve the original reader/writer access masks.
        handle = self.api.OpenProcess(0x400, False, self.proc_id)
        if not handle:
            raise Rejected(f"Cannot query Proton process information (WinError {ctypes.get_last_error()}).")
        try:
            peb = ctypes.c_size_t()
            returned = w.ULONG()
            status = function(handle, 26, ctypes.byref(peb), ctypes.sizeof(peb), ctypes.byref(returned))
            if status < 0 or returned.value not in (0, ctypes.sizeof(peb)):
                raise Rejected(f"Proton WoW64 PEB query failed (NTSTATUS 0x{status & 0xFFFFFFFF:08x}).")
            return peb.value
        finally:
            self.api.CloseHandle(handle)

    def module(self):
        self.validation_stage = "query_wow64_peb_and_image_headers"
        try:
            base, size, observation = image_from_wow64_peb(self.read, self._wow64_peb)
        except (OSError, Rejected) as exc:
            self.module_discovery = {"method": "WoW64 PEB32", "error": str(exc)}
            raise
        self.module_discovery = observation
        self.validation_stage = "validate_live_image_header"
        # The unchanged validate_process still requires the pinned preferred
        # image base and exact SizeOfImage before any patch-context checks.
        return base, size


class ProtonReader(ProtonImageQuery, WindowsReader):
    pass


class ProtonTrialProcess(ProtonImageQuery, WindowsTrialProcess):
    pass
