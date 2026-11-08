import struct
import unittest

from patch_candidate import Rejected
from proton_process import image_from_wow64_peb


class ProtonImageTests(unittest.TestCase):
    def setUp(self):
        self.peb = 0x7EFDF000
        self.base = 0x400000
        self.size = 21671936
        dos = bytearray(64)
        dos[:2] = b"MZ"
        struct.pack_into("<I", dos, 0x3C, 0x80)
        pe = bytearray(88)
        pe[:4] = b"PE\0\0"
        struct.pack_into("<HH", pe, 4, 0x14C, 7)
        struct.pack_into("<H", pe, 20, 0xE0)
        struct.pack_into("<H", pe, 24, 0x10B)
        struct.pack_into("<I", pe, 52, self.base)
        struct.pack_into("<I", pe, 80, self.size)
        self.memory = {self.peb + 8: struct.pack("<I", self.base), self.base: bytes(dos),
                       self.base + 0x80: bytes(pe)}

    def read(self, address, size):
        value = self.memory.get(address)
        if isinstance(value, list):
            value = value.pop(0)
        return value

    def query(self):
        return self.peb

    def module(self, query=None):
        return image_from_wow64_peb(self.read, query or self.query)

    def test_actual_base_and_size_come_from_the_selected_process(self):
        base, size, observation = self.module()
        self.assertEqual((base, size), (self.base, self.size))
        self.assertTrue(observation["root_stable"])
        self.assertEqual(observation["peb32"], hex(self.peb))

    def test_missing_non_wow64_or_invalid_peb_is_refused(self):
        for pointer in (None, 0, 0xFFFF, 0x100000000):
            with self.subTest(pointer=pointer), self.assertRaisesRegex(Rejected, "WoW64 PEB"):
                self.module(query=lambda: pointer)

    def test_unreadable_or_short_reads_are_not_guessed(self):
        original = dict(self.memory)
        for address in original:
            for value in (None, b"\0"):
                self.memory = dict(original)
                self.memory[address] = value
                with self.subTest(address=address, value=value), self.assertRaisesRegex(Rejected, "Cannot read"):
                    self.module()

    def test_invalid_dos_and_pe_headers_are_refused(self):
        mutations = ((self.base, 0, b"NO"),
                     (self.base, 0x3C, struct.pack("<I", 0x1001)),
                     (self.base + 0x80, 0, b"NO\0\0"),
                     (self.base + 0x80, 4, struct.pack("<H", 0x8664)),
                     (self.base + 0x80, 6, struct.pack("<H", 0)),
                     (self.base + 0x80, 20, struct.pack("<H", 0x20)),
                     (self.base + 0x80, 24, struct.pack("<H", 0x20B)),
                     (self.base + 0x80, 80, struct.pack("<I", 0)),
                     (self.base + 0x80, 80, struct.pack("<I", 12345)))
        original = dict(self.memory)
        for address, offset, value in mutations:
            self.memory = dict(original)
            changed = bytearray(self.memory[address])
            changed[offset:offset + len(value)] = value
            self.memory[address] = bytes(changed)
            with self.subTest(address=address, offset=offset), self.assertRaises(Rejected):
                self.module()

    def test_invalid_image_pointer_and_overflow_are_refused(self):
        for address in (0, 0xFFFF):
            self.memory[self.peb + 8] = struct.pack("<I", address)
            with self.subTest(address=address), self.assertRaisesRegex(Rejected, "image-base"):
                self.module()
        self.memory[self.peb + 8] = struct.pack("<I", self.base)
        pe = bytearray(self.memory[self.base + 0x80])
        struct.pack_into("<I", pe, 80, 0xFFFFF000)
        self.memory[self.base + 0x80] = bytes(pe)
        with self.assertRaisesRegex(Rejected, "image size"):
            self.module()

    def test_changed_peb_or_image_base_discards_the_module(self):
        pointers = iter([self.peb, self.peb + 0x1000])
        with self.assertRaisesRegex(Rejected, "changed"):
            self.module(query=lambda: next(pointers))
        self.memory[self.peb + 8] = [struct.pack("<I", self.base), struct.pack("<I", self.base + 0x1000)]
        with self.assertRaisesRegex(Rejected, "changed"):
            self.module()


if __name__ == "__main__":
    unittest.main()
