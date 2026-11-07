import copy
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

from patch_candidate import Rejected, candidate_bytes, digest, inspect_bytes, load_manifest, write_candidate
from probe_windows import snapshot


def fixture():
    data = bytearray(1024)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HH", data, 0x84, 0x14C, 1)
    struct.pack_into("<H", data, 0x94, 0xE0)
    struct.pack_into("<H", data, 0x98, 0x10B)
    struct.pack_into("<I", data, 0xB4, 0x400000)
    struct.pack_into("<IIII", data, 0x180, 0x100, 0x1000, 0x100, 0x200)
    data[0x210:0x214] = b"abcd"
    result = bytearray(data)
    result[0x210:0x214] = b"wxyz"
    spec = {"size_bytes": len(data), "input_sha256": digest(data),
            "candidate_sha256": digest(result), "machine": 0x14C, "image_base": 0x400000,
            "patches": [{"name": "fixture", "rva": 0x1010, "file_offset": 0x210,
                         "expected_hex": b"abcd".hex(), "replacement_hex": b"wxyz".hex(),
                         "context_offset": 0x200, "context_hex": data[0x200:0x220].hex()}]}
    return bytes(data), bytes(result), spec


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.data, self.expected, self.spec = fixture()

    def test_valid_candidate_changes_only_requested_bytes(self):
        self.assertEqual(candidate_bytes(self.data, self.spec), self.expected)
        self.assertFalse(inspect_bytes(self.data, self.spec)["gameplay_validated"])

    def test_wrong_build_and_already_patched_refused(self):
        for data in [self.data[:-1], self.expected, bytes(1024)]:
            with self.subTest(size=len(data)), self.assertRaises(Rejected):
                candidate_bytes(data, self.spec)

    def test_header_checked_after_hash(self):
        damaged = bytearray(self.data)
        damaged[0x98:0x9A] = b"\0\0"
        self.spec["input_sha256"] = digest(damaged)
        with self.assertRaisesRegex(Rejected, "architecture"):
            inspect_bytes(damaged, self.spec)

    def test_context_mutation_refused_even_with_matching_hash(self):
        damaged = bytearray(self.data)
        damaged[0x20F] = 1
        self.spec["input_sha256"] = digest(damaged)
        with self.assertRaisesRegex(Rejected, "Surrounding"):
            inspect_bytes(damaged, self.spec)

    def test_original_bytes_checked_independently(self):
        self.spec["patches"][0]["expected_hex"] = b"1234".hex()
        with self.assertRaisesRegex(Rejected, "Original"):
            inspect_bytes(self.data, self.spec)

    def test_inconsistent_rva_refused(self):
        self.spec["patches"][0]["rva"] += 1
        with self.assertRaisesRegex(Rejected, "mapping"):
            inspect_bytes(self.data, self.spec)

    def test_overlap_refused(self):
        self.spec["patches"] *= 2
        with self.assertRaisesRegex(Rejected, "Overlapping"):
            inspect_bytes(self.data, self.spec)

    def test_invalid_ranges_and_lengths_refused(self):
        for field, value in [("file_offset", -1), ("file_offset", 1023),
                             ("replacement_hex", ""), ("context_offset", -1)]:
            spec = copy.deepcopy(self.spec)
            spec["patches"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(Rejected):
                candidate_bytes(self.data, spec)

    def test_wrong_output_checksum_refused(self):
        self.spec["candidate_sha256"] = "0" * 64
        with self.assertRaisesRegex(Rejected, "output checksum"):
            candidate_bytes(self.data, self.spec)

    def test_original_preserved_and_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.exe"
            source.write_bytes(self.data)
            output = write_candidate(source, self.spec, tmp)
            self.assertEqual(source.read_bytes(), self.data)
            self.assertEqual(output.read_bytes(), self.expected)
            with self.assertRaises(FileExistsError):
                write_candidate(source, self.spec, tmp)
            self.assertEqual(output.read_bytes(), self.expected)

    def test_input_equal_output_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "private" / "BH6.native-candidate.exe"
            source.parent.mkdir()
            source.write_bytes(self.data)
            with self.assertRaisesRegex(Rejected, "must differ"):
                write_candidate(source, self.spec, tmp)
            self.assertEqual(source.read_bytes(), self.data)

    @unittest.skipIf(os.name == "nt", "Symlink creation may require a Windows privilege")
    def test_symlink_output_escape_refused(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            source = Path(tmp) / "input.exe"
            source.write_bytes(self.data)
            (Path(tmp) / "private").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(Rejected, "escapes"):
                write_candidate(source, self.spec, tmp)
            self.assertFalse((Path(outside) / "BH6.native-candidate.exe").exists())


class ObservationTests(unittest.TestCase):
    def test_unreadable_memory_stays_unknown(self):
        spec = load_manifest()
        report = snapshot(lambda address, size: None, 0x400000, spec, b"")
        self.assertIsNone(report["timer_field_candidate"])
        self.assertIsNone(report["stage_field_candidate"])
        self.assertTrue(all(p["live_hex"] is None for p in report["native_sites"]))
        self.assertNotIn("PASS", report["status"])

    def test_memory_mutation_and_candidate_are_distinguished(self):
        spec = load_manifest()
        patch = spec["patches"][0]
        def read(address, size):
            if address == 0x400000 + patch["rva"]:
                return bytes.fromhex(patch["replacement_hex"])
            return None
        report = snapshot(read, 0x400000, spec, b"")
        self.assertTrue(report["native_sites"][0]["matches_candidate"])
        self.assertFalse(report["native_sites"][0]["matches_original"])

    def test_nonfinite_float_does_not_corrupt_json(self):
        spec = load_manifest()
        root = 0x20000000
        locations = {0x400000 + spec["probe_candidates"]["game_info_root_rva"]: struct.pack("<I", root),
                     root - 0x794: struct.pack("<f", float("nan"))}
        report = snapshot(lambda address, size: locations.get(address), 0x400000, spec, b"")
        self.assertIsNone(report["timer_field_candidate"])
        json.dumps(report, allow_nan=False)

    def test_native_timer_uses_mode_object_without_assuming_heap_adjacency(self):
        spec = load_manifest()
        candidates = spec["probe_candidates"]
        info, mode = 0x20000000, 0x30000000
        locations = {
            0x400000 + candidates["game_info_root_rva"]: struct.pack("<I", info),
            0x400000 + candidates["mode_root_rva"]: struct.pack("<I", mode),
            info - 0x794: struct.pack("<f", 0.0),
            mode + 0x486c: struct.pack("<f", 117.5),
            mode + 0x4874: struct.pack("<f", 2.5),
            mode + 0x4864: struct.pack("<I", 0),
        }
        report = snapshot(lambda address, size: locations.get(address), 0x400000, spec, b"")
        self.assertEqual(report["timer_field_candidate"], 0.0)
        self.assertEqual(report["native_timer_field_candidate"], 117.5)
        self.assertEqual(report["native_elapsed_field_candidate"], 2.5)
        self.assertFalse(report["timer_candidates_same_address"])

    def test_timer_address_equality_and_nonfinite_native_values(self):
        spec = load_manifest()
        candidates = spec["probe_candidates"]
        mode, info = 0x20000000, 0x20005000
        locations = {
            0x400000 + candidates["game_info_root_rva"]: struct.pack("<I", info),
            0x400000 + candidates["mode_root_rva"]: struct.pack("<I", mode),
            mode + 0x486c: struct.pack("<f", float("inf")),
            mode + 0x4874: struct.pack("<f", float("nan")),
        }
        report = snapshot(lambda address, size: locations.get(address), 0x400000, spec, b"")
        self.assertTrue(report["timer_candidates_same_address"])
        self.assertIsNone(report["native_timer_field_candidate"])
        self.assertIsNone(report["native_elapsed_field_candidate"])
        json.dumps(report, allow_nan=False)


@unittest.skipUnless(os.environ.get("RE6_TEST_INPUT"), "Private executable fixture not supplied")
class PrivateExecutableTests(unittest.TestCase):
    def test_actual_input_candidate_diff_and_guards(self):
        path = Path(os.environ["RE6_TEST_INPUT"])
        data = path.read_bytes()
        spec = load_manifest()
        result = candidate_bytes(data, spec)
        allowed = set()
        for patch in spec["patches"]:
            start = patch["file_offset"]
            allowed.update(range(start, start + len(bytes.fromhex(patch["expected_hex"]))))
        changed = {i for i, (a, b) in enumerate(zip(data, result)) if a != b}
        self.assertTrue(changed)
        self.assertTrue(changed <= allowed)
        self.assertEqual(digest(result), spec["candidate_sha256"])
        self.assertEqual(digest(path.read_bytes()), spec["input_sha256"])
        with self.assertRaises(Rejected):
            inspect_bytes(result, spec)


if __name__ == "__main__":
    unittest.main()
