import copy
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from patch_candidate import ROOT, Rejected, load_manifest
import steam_patch as launcher
from test_native_trial import Memory, menu_observation, synthetic_image


class FrozenBuildTests(unittest.TestCase):
    def test_tested_runtime_and_patch_specification_are_unchanged(self):
        frozen = json.loads((ROOT / "docs/tested-build.json").read_text())
        for name, expected in frozen["runtime_file_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)
        spec = load_manifest()
        for key, expected in frozen["patch_specification"].items():
            self.assertEqual(spec[key], expected, key)
        self.assertEqual(launcher.pinned_manifest(), spec)

    def test_wrapper_rejects_changed_patch_even_with_a_new_output_checksum(self):
        spec = copy.deepcopy(load_manifest())
        spec["patches"][0]["replacement_hex"] = "83c003"
        spec["candidate_sha256"] = "0" * 64
        with patch.object(launcher, "load_manifest", return_value=spec):
            with self.assertRaisesRegex(Rejected, "frozen"):
                launcher.pinned_manifest()


class SteamDiscoveryTests(unittest.TestCase):
    def test_vdf_comments_case_and_escaped_paths(self):
        value = launcher.parse_vdf(r'''// before
            "LibraryFolders" { "0" { "path" "D:\\Steam Library" "apps" { "221040" "1" } }
            "1" "E:\\Older Library" } // after
        ''')
        self.assertEqual(value["libraryfolders"]["0"]["path"], r"D:\Steam Library")
        self.assertEqual(value["libraryfolders"]["1"], r"E:\Older Library")

    def test_malformed_or_ambiguous_vdf_refused(self):
        for value in ('"a" {', '"a"', '"a" }', '} a b', '"a" "1" "A" "2"',
                      '"a" "unterminated', '{ a b }', 'a {' * 34 + '}' * 34):
            with self.subTest(value=value), self.assertRaises(Rejected):
                launcher.parse_vdf(value)

    def make_install(self, root, name="Resident Evil 6", appid="221040"):
        steamapps = root / "steamapps"
        executable = steamapps / "common" / name / "BH6.exe"
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.touch()
        (steamapps / "appmanifest_221040.acf").write_text(
            f'"AppState" {{ "appid" "{appid}" "installdir" "{name}" }}', encoding="utf-8")
        return executable.resolve()

    def test_default_and_secondary_library_and_duplicate_roots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Steam"
            secondary = Path(directory) / "Games Library"
            first = self.make_install(root)
            second = self.make_install(secondary)
            escaped = str(secondary).replace("\\", "\\\\")
            (root / "steamapps/libraryfolders.vdf").write_text(
                f'"libraryfolders" {{ "0" {{ "path" "{escaped}" }} "1" "{escaped}" }}')
            self.assertEqual(set(launcher.discover_installs([root, root])), {first, second})
            self.assertEqual(launcher.discover_installs([Path(directory) / "Missing"]), [])

    def test_wrong_appid_and_traversal_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = self.make_install(root, appid="123")
            with self.assertRaisesRegex(Rejected, "app ID"):
                launcher.discover_installs([root])
            manifest = root / "steamapps/appmanifest_221040.acf"
            for name in ("..", "../copy", "D:/copy", "D:\\\\copy", ""):
                manifest.write_text(f'"AppState" {{ "appid" "221040" "installdir" "{name}" }}')
                with self.subTest(name=name), self.assertRaisesRegex(Rejected, "unsafe"):
                    launcher.discover_installs([root])
            self.assertTrue(executable.exists())

    def test_exactly_one_game_process_required(self):
        self.assertEqual(launcher.choose_pid([(9, "steam.exe"), (45, "BH6.exe")]), 45)
        for processes in ([], [(1, "BH6.exe"), (2, "bh6.EXE")], [(1, "notBH6.exe")]):
            with self.assertRaises(Rejected):
                launcher.choose_pid(processes)

    def test_test_copy_is_rejected_before_core_validation(self):
        reader = unittest.mock.Mock()
        reader.image_path.return_value = Path("/other-copy/BH6.exe")
        with patch.object(launcher, "validate_process") as validate:
            with self.assertRaisesRegex(Rejected, "registered"):
                launcher.validate_steam_process(reader, {}, [Path("/steam/common/RE6/BH6.exe")])
            validate.assert_not_called()


class WrapperTransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.candidate, cls.spec = synthetic_image()

    def setUp(self):
        self.memory = Memory(self.original)
        self.paused = False
        self.closed = False
        self.pause_count = 0
        self.validation_count = 0
        self.observation = menu_observation()

    def close(self):
        self.closed = True

    def read(self, address, size):
        if address == 0x400000 + self.spec["probe_candidates"]["player_manager_root_rva"]:
            return b"\0" * 4
        return self.memory.read(address, size)

    def write_code(self, address, value):
        self.assertTrue(self.paused, "Wrapper must hold the original backend suspension")
        self.memory.write(address, value)

    @contextmanager
    def suspended(self):
        self.pause_count += 1
        self.paused = True
        try:
            yield
        finally:
            self.paused = False

    def validate(self, reader, spec, installs):
        self.validation_count += 1
        return 0x400000, self.original

    def action(self, action, logs):
        with patch.multiple(launcher, pinned_manifest=lambda: self.spec, steam_roots=lambda: [],
                            discover_installs=lambda _: [Path("/steam/BH6.exe")],
                            running_processes=lambda: [(10, "BH6.exe")],
                            WindowsReader=lambda _: self, WindowsTrialProcess=lambda _: self,
                            validate_steam_process=self.validate,
                            snapshot=lambda *args: copy.deepcopy(self.observation),
                            audit_directory=lambda: logs):
            return launcher.run_action(action)

    def test_apply_restore_reuses_transaction_and_does_not_change_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            logs = Path(directory)
            result = self.action("apply", logs)
            self.assertEqual(result["state"], "applied")
            self.assertEqual(self.memory.data, self.candidate)
            self.assertEqual(self.validation_count, 2)
            self.assertEqual(self.pause_count, 1)
            self.assertFalse(self.paused)
            self.assertTrue(self.closed)
            self.assertEqual(len(list(logs.glob("apply-*.json"))), 1)
            self.action("restore", logs)
            self.assertEqual(self.memory.data, self.original)

    def test_existing_lobby_rejected_under_suspension_before_any_writes(self):
        self.observation["session"]["fields"]["session_type_candidate"] = 1
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(Rejected, "host/join"):
                self.action("apply", Path(directory))
        self.assertEqual(self.memory.writes, [])
        self.assertEqual(self.pause_count, 1)
        self.assertFalse(self.paused)
        self.assertTrue(self.closed)

    def test_inspection_in_occupied_lobby_is_read_only_and_keeps_applied_status(self):
        self.memory.data[:] = self.candidate
        self.observation["session"]["fields"]["session_type_candidate"] = 1
        self.observation["session"]["slots"][1]["slot_state"] = 1
        with tempfile.TemporaryDirectory() as directory:
            result = self.action("inspect", Path(directory))
            self.assertEqual(list(Path(directory).iterdir()), [])
        self.assertEqual(result["state"], "applied")
        self.assertFalse(result["can_change"])
        self.assertEqual(self.pause_count, 0)
        self.assertEqual(self.memory.writes, [])

    def test_guard_failure_and_partial_write_roll_back_without_suppressing_errors(self):
        self.memory.data[self.spec["patches"][0]["context_offset"]] ^= 1
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(Rejected, "context"):
                self.action("apply", Path(directory))
        self.assertEqual(self.memory.writes, [])
        self.memory = Memory(self.original)
        real_write = self.write_code
        count = 0

        def partial_write(address, value):
            nonlocal count
            count += 1
            if count == 2:
                real_write(address, value[:1])
                raise OSError("simulated partial failure")
            real_write(address, value)

        self.write_code = partial_write
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(Rejected, "previous bytes restored"):
                self.action("apply", Path(directory))
        self.assertEqual(self.memory.data, self.original)
        self.assertFalse(self.paused)


if __name__ == "__main__":
    unittest.main()
