import copy
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import struct
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
            with self.assertRaisesRegex(Rejected, "file identity"):
                launcher.validate_steam_process(reader, {}, [Path("/steam/common/RE6/BH6.exe")])
            validate.assert_not_called()

    def test_file_identity_alias_passes_but_still_requires_core_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            registered = Path(directory) / "BH6.exe"
            registered.write_bytes(b"synthetic image")
            alias = Path(directory) / "Alias.exe"
            alias.hardlink_to(registered)
            reader = unittest.mock.Mock()
            reader.image_path.return_value = alias
            with patch.object(launcher, "validate_process", return_value=(123, b"disk")) as validate:
                self.assertEqual(launcher.validate_steam_process(reader, {}, [registered]), (123, b"disk"))
                validate.assert_called_once_with(reader, {})

    def test_separate_copy_with_identical_content_is_not_a_registered_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            registered = Path(directory) / "BH6.exe"
            registered.write_bytes(b"same synthetic bytes")
            copy = Path(directory) / "Separate.exe"
            copy.write_bytes(registered.read_bytes())
            reader = unittest.mock.Mock()
            reader.image_path.return_value = copy
            with patch.object(launcher, "validate_process") as validate:
                with self.assertRaisesRegex(Rejected, "file identity"):
                    launcher.validate_steam_process(reader, {}, [registered])
                validate.assert_not_called()


class InactiveSessionTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_manifest()
        self.reader = unittest.mock.Mock()
        self.reader.read.return_value = struct.pack("<I", 0x22000000)

    def check(self, observation):
        launcher.inactive_session_check(self.reader, 0x400000, self.spec, observation)

    def test_no_scene_value_or_scene_readability_is_required(self):
        for stage in (None, 0, 904, 1102, 1212, 0xFFFFFFFF):
            for session_type in (0, 4):
                with self.subTest(stage=stage, session_type=session_type):
                    observation = menu_observation()
                    observation["stage_field_candidate"] = stage
                    observation["scene_selection"] = {"stage": None, "root_stable": False}
                    observation["session"]["fields"]["session_type_candidate"] = session_type
                    self.check(observation)

    def test_active_or_unknown_session_players_and_any_slot_are_refused(self):
        mutations = (
            lambda o: o["session"].update(root_stable=False),
            lambda o: o["session"].update(root_stable=None),
            lambda o: o["session"].update(fields=None),
            lambda o: o["session"]["fields"].update(session_type_candidate=1),
            lambda o: o["session"]["fields"].update(session_type_candidate=2),
            lambda o: o["session"]["fields"].update(session_type_candidate=None),
            lambda o: o["session"].update(slots=None),
            lambda o: o["session"].update(slots=[]),
            lambda o: o["session"]["slots"][0].update(slot_state=2),
            lambda o: o["session"]["slots"][1].update(slot_state=1),
            lambda o: o["session"]["slots"][7].update(slot_state=None),
            lambda o: o["player_objects"].update(root_stable=False),
            lambda o: o["player_objects"].update(entry_present=None),
            lambda o: o["player_objects"].update(entry_present=[True] + [False] * 7),
            lambda o: o["player_objects"].update(entry_present=[None] * 8),
        )
        for mutation in mutations:
            observation = menu_observation()
            observation["stage_field_candidate"] = 904
            mutation(observation)
            with self.subTest(observation=observation), self.assertRaises(Rejected):
                self.check(observation)

    def test_readable_null_manager_is_distinct_from_invalid_or_failed_reads(self):
        observation = menu_observation()
        observation["player_objects"].update(root_stable=None, entry_present=None)
        self.reader.read.return_value = b"\0" * 4
        self.check(observation)
        for data in (None, b"\0", struct.pack("<I", 0xFFFF), b"\xff" * 4):
            self.reader.read.return_value = data
            with self.subTest(data=data), self.assertRaises(Rejected):
                self.check(observation)
        self.reader.read.return_value = b"\0" * 4
        observation["player_objects"]["entry_present"] = [True] + [False] * 7
        with self.assertRaises(Rejected):
            self.check(observation)


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
        self.info_root = 0x21000000
        self.info_index = 0
        self.record_stages = [1102] * 4
        self.scene_unreadable = False
        self.on_suspend = lambda: None

    def close(self):
        self.closed = True

    def image_path(self):
        return Path("/steam/BH6.exe")

    def read(self, address, size):
        if address == 0x400000 + self.spec["probe_candidates"]["game_info_root_rva"]:
            return None if self.scene_unreadable else struct.pack("<I", self.info_root)
        if address == self.info_root + 0x20:
            return struct.pack("<I", self.info_index)
        for index, stage in enumerate(self.record_stages):
            if address == self.info_root + 0x412A4 + index * 0x3CE4:
                return struct.pack("<I", stage)
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
            self.on_suspend()
            yield
        finally:
            self.paused = False

    def validate(self, reader, spec, installs):
        self.validation_count += 1
        return 0x400000, self.original

    def action(self, action, logs, run_action=launcher.run_action):
        with patch.multiple(launcher, pinned_manifest=lambda: self.spec, steam_roots=lambda: [],
                            discover_installs=lambda _: [Path("/steam/BH6.exe")],
                            running_processes=lambda: [(10, "BH6.exe")],
                            WindowsReader=lambda _: self, WindowsTrialProcess=lambda _: self,
                            validate_steam_process=self.validate,
                            snapshot=lambda *args: copy.deepcopy(self.observation),
                            audit_directory=lambda: logs):
            return run_action(action)

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

    def test_nonzero_record_menu_can_apply_exact_patch_when_record_zero_is_stale(self):
        self.info_index = 1
        self.record_stages[0] = 0
        self.observation["stage_field_candidate"] = 0
        with tempfile.TemporaryDirectory() as directory:
            inspection = self.action("inspect", Path(directory))
            self.assertTrue(inspection["can_change"])
            observation = inspection["observation"]
            self.assertEqual(observation["stage_field_candidate"], 1102)
            self.assertEqual(observation["legacy_unindexed_stage_field_candidate"], 0)
            self.assertEqual(observation["scene_selection"]["record_index"], 1)
            self.action("apply", Path(directory))
        self.assertEqual(self.memory.data, self.candidate)
        self.assertFalse(self.paused)

    def test_gameplay_slots_refuse_writes_independent_of_scene(self):
        self.info_index = 1
        self.record_stages[1] = 1212
        self.observation["session"]["slots"][0]["slot_state"] = 2
        with tempfile.TemporaryDirectory() as directory:
            inspection = self.action("inspect", Path(directory))
            self.assertFalse(inspection["can_change"])
            self.assertIn("slots", inspection["reason"])
            with self.assertRaisesRegex(Rejected, "slots"):
                self.action("apply", Path(directory))
        self.assertEqual(self.memory.writes, [])
        self.assertFalse(self.paused)

    def test_reported_scene_904_idle_state_applies_and_restores_the_exact_bytes(self):
        self.record_stages[0] = 904
        self.observation["stage_field_candidate"] = 904
        self.observation["session"]["fields"]["session_type_candidate"] = 0
        with tempfile.TemporaryDirectory() as directory:
            inspection = self.action("inspect", Path(directory))
            self.assertEqual(inspection["observation"]["stage_field_candidate"], 904)
            self.assertTrue(inspection["can_change"])
            self.action("apply", Path(directory))
            self.assertEqual(self.memory.data, self.candidate)
            self.action("restore", Path(directory))
            self.assertEqual(self.memory.data, self.original)

    def test_unreadable_scene_does_not_block_an_independently_verified_idle_session(self):
        self.scene_unreadable = True
        with tempfile.TemporaryDirectory() as directory:
            inspection = self.action("inspect", Path(directory))
            self.assertIsNone(inspection["observation"]["stage_field_candidate"])
            self.assertTrue(inspection["can_change"])
            self.action("apply", Path(directory))
        self.assertEqual(self.memory.data, self.candidate)

    def test_session_that_becomes_active_after_refresh_is_refused_under_suspension(self):
        with tempfile.TemporaryDirectory() as directory:
            inspection = self.action("inspect", Path(directory))
            self.assertTrue(inspection["can_change"])
            self.on_suspend = lambda: self.observation["session"]["slots"][0].update(slot_state=2)
            with self.assertRaisesRegex(Rejected, "slots"):
                self.action("apply", Path(directory))
        self.assertEqual(self.memory.writes, [])
        self.assertFalse(self.paused)
        self.assertTrue(self.closed)

    def test_diagnostics_export_is_read_only_and_records_the_rejected_scene(self):
        self.info_index = 2
        self.record_stages[2] = 1212
        self.observation["session"]["slots"][0]["slot_state"] = 2
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "report.json"
            with patch.object(launcher, "run_action", side_effect=lambda action: self.action(action, Path(directory))) as run:
                launcher.save_diagnostics(destination)
                run.assert_called_once_with("inspect")
            report = json.loads(destination.read_text())
            self.assertEqual(report["access"], "READ ONLY")
            self.assertEqual(report["launcher_version"], launcher.VERSION)
            self.assertFalse(report["can_change"])
            self.assertEqual(report["observation"]["scene_selection"]["record_index"], 2)
            self.assertEqual(report["observation"]["stage_field_candidate"], 1212)
        self.assertEqual(self.memory.writes, [])
        self.assertEqual(self.pause_count, 0)

    def test_failed_identity_inspection_can_be_exported_without_enabling_writes(self):
        def reject(reader, spec, installs):
            raise Rejected("file identity mismatch for synthetic alias")
        self.validate = reject
        with tempfile.TemporaryDirectory() as directory:
            report = self.action("inspect", Path(directory))
            self.assertEqual(report["state"], "unverified")
            self.assertFalse(report["can_change"])
            self.assertFalse(report["executable_identity_verified"])
            self.assertIn("BH6.exe", report["process_image_path"])
            self.assertTrue(report["registered_executable_paths"])
            self.assertIn("file identity mismatch", report["error"])
            with self.assertRaisesRegex(Rejected, "file identity mismatch"):
                self.action("apply", Path(directory))
        self.assertEqual(self.memory.writes, [])
        self.assertEqual(self.pause_count, 0)
        self.assertTrue(self.closed)

    def test_diagnostics_cannot_overwrite_files_or_use_non_json_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "existing.json"
            destination.write_text("keep")
            with patch.object(launcher, "run_action", return_value={}) as run:
                with self.assertRaisesRegex(Rejected, ".json"):
                    launcher.save_diagnostics(destination.with_suffix(".exe"))
                run.assert_not_called()
                with self.assertRaises(FileExistsError):
                    launcher.save_diagnostics(destination)
            self.assertEqual(destination.read_text(), "keep")

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
