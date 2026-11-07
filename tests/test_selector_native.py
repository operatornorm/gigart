"""Exercise the candidate's 27-byte x86 selector on Linux x86-64.

This is NOT a 32-bit game/ABI test. The selector's register-width instructions
have the same encodings in long mode; its memory operand uses a low address.
The surrounding game and RNG are replaced by a bounded synthetic fixture.
"""
import ctypes
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from patch_candidate import load_manifest


ASM = r""".text
.globl run_selector
.type run_selector,@function
run_selector:
    push %rbx
    push %r13
    push %r14
    mov %esi, %ebx
    mov %rdx, %r13
    mov %rcx, %r14
    xor %r8d, %r8d
.Lretry:
    mov $0x186dea4, %ecx
    call .Lrng
    .incbin "selector.bin"
.Lfinish:
    mov %r8, %rax
    shl $32, %rax
    mov %ecx, %edx
    or %rdx, %rax
    pop %r14
    pop %r13
    pop %rbx
    ret
.Lrng:
    cmp %r14, %r8
    jae .Lexhausted
    mov (%r13,%r8,4), %eax
    inc %r8
    ret
.Lexhausted:
    # Discard only the synthetic RNG return address, then report exhaustion.
    add $8, %rsp
    mov $-1, %ecx
    jmp .Lfinish
.size run_selector, .-run_selector
.section .note.GNU-stack,"",@progbits
"""


@unittest.skipUnless(sys.platform == "linux" and platform.machine() == "x86_64"
                     and shutil.which("cc"), "Needs Linux x86-64 and the existing C compiler")
class NativeSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        directory = Path(cls.directory.name)
        patch = next(p for p in load_manifest()["patches"] if p["name"] == "slot_assignment")
        code = bytes.fromhex(patch["replacement_hex"])
        # Execute only this audited original candidate, never arbitrary manifest
        # contents or bytes taken from a supplied game executable.
        if code.hex() != "31d28b4f4cf7f189d1b801000000d3e085c375e2eb059090909090":
            raise AssertionError("Selector bytes changed; audit the fixture before execution")
        (directory / "selector.bin").write_bytes(code)
        (directory / "selector.S").write_text(ASM)
        build = subprocess.run([shutil.which("cc"), "-shared", "-fPIC", "-Wl,-z,noexecstack",
                                "selector.S", "-o", "selector.so"], cwd=directory,
                               capture_output=True, text=True)
        if build.returncode:
            raise AssertionError(f"Selector fixture build failed: {build.stderr}")
        cls.library = ctypes.CDLL(str(directory / "selector.so"))
        cls.native = cls.library.run_selector
        cls.native.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                               ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t]
        cls.native.restype = ctypes.c_uint64
        cls.libc = ctypes.CDLL(None, use_errno=True)
        cls.libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_int, ctypes.c_long]
        cls.libc.mmap.restype = ctypes.c_void_p
        cls.libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        cls.libc.munmap.restype = ctypes.c_int

    def setUp(self):
        # MAP_PRIVATE | MAP_ANONYMOUS | MAP_32BIT: keep RDI's object address in
        # the range where 32- and 64-bit addressing produce the same operand.
        self.address = self.libc.mmap(None, 4096, 3, 0x22 | 0x40, -1, 0)
        self.assertNotIn(self.address, (None, ctypes.c_void_p(-1).value))
        self.addCleanup(self.libc.munmap, self.address, 4096)
        self.assertLess(self.address + 4096, 1 << 32)

    def select(self, count, occupied, draws):
        ctypes.c_uint32.from_address(self.address + 0x4C).value = count
        before = ctypes.string_at(self.address, 4096)
        data = (ctypes.c_uint32 * len(draws))(*draws)
        result = self.native(self.address, occupied, data, len(draws))
        self.assertEqual(ctypes.string_at(self.address, 4096), before)
        return result & 0xFFFFFFFF, result >> 32

    def test_every_occupancy_mask_and_unsigned_rng_edges(self):
        cases = 0
        for count in (2, 4, 6):
            for occupied in range(1 << count):
                for first in (*range(count), 0xFFFFFFFF, 0x80000000):
                    draws = [first, *range(count)]
                    expected = next(((value % count, i+1) for i, value in enumerate(draws)
                                     if not occupied & (1 << (value % count))),
                                    (0xFFFFFFFF, len(draws)))
                    with self.subTest(count=count, mask=occupied, first=first):
                        self.assertEqual(self.select(count, occupied, draws), expected)
                    cases += 1
        self.assertEqual(cases, 624)

    def test_retries_after_repeated_occupied_draws(self):
        # Regression for the native backward branch reaching the RNG call,
        # rather than cycling without drawing another value.
        self.assertEqual(self.select(6, 0b001111, [0]*20 + [3, 4]), (4, 22))

    def test_full_mask_exhausts_synthetic_rng_instead_of_claiming_success(self):
        # The real candidate has an unbounded retry. The fixture bounds ONLY
        # its RNG input, so a full mask or adversarial RNG can be tested safely.
        self.assertEqual(self.select(6, 0b111111, list(range(6))*3), (0xFFFFFFFF, 18))


if __name__ == "__main__":
    unittest.main()
