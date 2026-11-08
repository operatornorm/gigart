import os
from pathlib import Path
import struct
import unittest

from menu_state import RECORD_COUNT, RECORD_STRIDE, selected_scene
from patch_candidate import Rejected, inspect_bytes, load_manifest
from steam_patch import menu_check
from test_native_trial import menu_observation


class SelectedSceneTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_manifest()
        self.base = 0x400000
        self.root_address = self.base + self.spec["probe_candidates"]["game_info_root_rva"]
        self.root = 0x20000000
        self.values = {self.root_address: self.root, self.root + 0x20: 0}
        self.reads = []
        for index in range(RECORD_COUNT):
            self.values[self.root + 0x412A4 + index * RECORD_STRIDE] = 1102

    def read(self, address, size):
        self.assertEqual(size, 4)
        self.reads.append(address)
        value = self.values.get(address)
        if isinstance(value, list):
            value = value.pop(0)
        return struct.pack("<I", value) if isinstance(value, int) else value

    def scene(self):
        return selected_scene(self.read, self.base, self.spec)

    def test_reads_each_of_four_native_records(self):
        for index in range(4):
            with self.subTest(index=index):
                self.values[self.root + 0x20] = index
                scene = self.scene()
                self.assertEqual(scene["stage"], 1102)
                self.assertEqual(scene["record_index"], index)
                self.assertTrue(scene["root_stable"])
                self.assertTrue(scene["record_index_stable"])

    def test_selected_record_controls_guard_in_both_directions(self):
        self.values[self.root + 0x20] = 1
        self.values[self.root + 0x412A4] = 0
        observation = menu_observation()
        observation["scene_selection"] = self.scene()
        observation["stage_field_candidate"] = observation["scene_selection"]["stage"]
        menu_check(self, self.base, self.spec, observation)
        self.values[self.root + 0x412A4] = 1102
        self.values[self.root + 0x412A4 + RECORD_STRIDE] = 1212
        observation["scene_selection"] = self.scene()
        observation["stage_field_candidate"] = observation["scene_selection"]["stage"]
        with self.assertRaisesRegex(Rejected, "1212"):
            menu_check(self, self.base, self.spec, observation)

    def test_invalid_roots_indices_and_short_reads_cannot_fall_back_to_record_zero(self):
        for value in (None, 0, 0xFFFF, 0xFFFFFFFF, b"\x00"):
            with self.subTest(root=value):
                self.values[self.root_address] = value
                self.assertIsNone(self.scene()["stage"])
        self.values[self.root_address] = self.root
        for index in (None, 4, 0xFFFFFFFF, b"\x00"):
            with self.subTest(index=index):
                self.values[self.root + 0x20] = index
                self.reads.clear()
                scene = self.scene()
                self.assertIsNone(scene["stage"])
                self.assertNotIn(self.root + 0x412A4, self.reads)
                observation = menu_observation()
                observation["scene_selection"] = scene
                with self.assertRaisesRegex(Rejected, "unreadable or changing"):
                    menu_check(self, self.base, self.spec, observation)

    def test_unreadable_selected_stage_is_unknown_even_when_record_zero_is_menu(self):
        self.values[self.root + 0x20] = 1
        for value in (None, b"\x4e\x04"):
            self.values[self.root + 0x412A4 + RECORD_STRIDE] = value
            scene = self.scene()
            self.assertEqual(scene["record_zero_stage"], 1102)
            self.assertIsNone(scene["stage"])

    def test_changed_or_lost_root_and_index_discard_the_scene(self):
        for address, values in ((self.root_address, [self.root, self.root + 0x1000]),
                                (self.root_address, [self.root, None]),
                                (self.root + 0x20, [0, 1]),
                                (self.root + 0x20, [0, None])):
            with self.subTest(address=address, values=values):
                self.values[self.root_address] = self.root
                self.values[self.root + 0x20] = 0
                self.values[address] = values
                scene = self.scene()
                self.assertIsNone(scene["stage"])
                self.assertIsNone(scene["record_zero_stage"])


@unittest.skipUnless(os.environ.get("RE6_TEST_INPUT"), "Private executable fixture not supplied")
class NativeSceneLayoutTests(unittest.TestCase):
    def test_layout_is_supported_by_pinned_getter_and_four_record_constructor(self):
        data = Path(os.environ["RE6_TEST_INPUT"]).read_bytes()
        inspect_bytes(data, load_manifest())

        def instructions(va, size):
            start = va - 0x400000 - 0xC00
            return data[start:start + size].hex()

        self.assertEqual(instructions(0x455380, 17), "8b412069c0e43c00008b8408a4120400c3")
        self.assertEqual(instructions(0x5682A8, 27),
                         "8dbe98f70300bb030000008bcfe8967d800081c7e43c00004b79f0")


if __name__ == "__main__":
    unittest.main()
