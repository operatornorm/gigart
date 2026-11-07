import copy
import ctypes
import struct
import unittest

from native_trial import (WindowsTrialProcess, apply_transaction, lobby_assessment,
                          mutation_plan, require_idle_menu)
from patch_candidate import Rejected, digest, load_manifest


def synthetic_image():
    spec = load_manifest()
    data = bytearray(0x700400)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HH", data, 0x84, 0x14C, 1)
    struct.pack_into("<H", data, 0x94, 0xE0)
    struct.pack_into("<H", data, 0x98, 0x10B)
    struct.pack_into("<I", data, 0xB4, 0x400000)
    struct.pack_into("<IIII", data, 0x178 + 8, 0x700000, 0x1000, 0x700000, 0x400)
    for patch in spec["patches"]:
        value = bytes.fromhex(patch["context_hex"])
        start = patch["context_offset"]
        data[start:start + len(value)] = value
    spec["size_bytes"] = len(data)
    spec["input_sha256"] = digest(data)
    candidate = bytearray(data)
    for patch in spec["patches"]:
        value = bytes.fromhex(patch["replacement_hex"])
        start = patch["file_offset"]
        candidate[start:start + len(value)] = value
    spec["candidate_sha256"] = digest(candidate)
    return bytes(data), bytes(candidate), spec


class Memory:
    def __init__(self, data):
        self.data = bytearray(data)
        self.writes = []

    def read(self, address, size):
        start = address - 0x400000 - 0xC00
        return bytes(self.data[start:start + size]) if start >= 0 else None

    def write(self, address, value):
        self.writes.append((address, value))
        start = address - 0x400000 - 0xC00
        self.data[start:start + len(value)] = value


class TransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.candidate, cls.spec = synthetic_image()

    def setUp(self):
        self.memory = Memory(self.original)

    def plan(self, restore=False):
        return mutation_plan(self.memory.read, 0x400000, self.original, self.spec, restore)

    def test_apply_restore_exact_bytes_without_disk_changes(self):
        apply_transaction(self.memory.read, self.memory.write, self.plan())
        self.assertEqual(self.memory.data, self.candidate)
        apply_transaction(self.memory.read, self.memory.write, self.plan(restore=True))
        self.assertEqual(self.memory.data, self.original)
        self.assertEqual(digest(self.original), self.spec["input_sha256"])

    def test_context_damage_aborts_entire_preflight(self):
        patch = self.spec["patches"][2]
        self.memory.data[patch["context_offset"]] ^= 0xFF
        with self.assertRaisesRegex(Rejected, "context"):
            self.plan()
        self.assertEqual(self.memory.writes, [])

    def test_mixed_state_and_relocated_base_refused(self):
        patch = self.spec["patches"][0]
        self.memory.write(0x400000 + patch["rva"], bytes.fromhex(patch["replacement_hex"]))
        for restore in (False, True):
            with self.assertRaises(Rejected):
                self.plan(restore)
        with self.assertRaisesRegex(Rejected, "Relocated"):
            mutation_plan(Memory(self.original).read, 0x500000, self.original, self.spec)

    def test_wrong_output_hash_or_legacy_modification_refused(self):
        spec = copy.deepcopy(self.spec)
        spec["candidate_sha256"] = "0"*64
        with self.assertRaisesRegex(Rejected, "checksum"):
            mutation_plan(self.memory.read, 0x400000, self.original, spec)
        self.memory.write(0x400000 + 0x60F51D, b"bad")
        with self.assertRaisesRegex(Rejected, "Historical"):
            self.plan()

    def test_prewrite_drift_is_refused_without_writes(self):
        plan = self.plan()
        self.memory.data[self.spec["patches"][0]["file_offset"]] ^= 1
        with self.assertRaisesRegex(Rejected, "before transaction"):
            apply_transaction(self.memory.read, self.memory.write, plan)
        self.assertEqual(self.memory.writes, [])

    def test_partial_write_rolls_back_all_attempted_spans(self):
        calls = 0
        def write(address, value):
            nonlocal calls
            calls += 1
            if calls == 2:
                self.memory.write(address, value[:2])
                raise OSError("simulated partial write")
            self.memory.write(address, value)
        with self.assertRaisesRegex(Rejected, "previous bytes restored"):
            apply_transaction(self.memory.read, write, self.plan())
        self.assertEqual(self.memory.data, self.original)
        self.assertEqual(calls, 4)

    def test_bad_readback_rolls_back(self):
        calls = 0
        def write(address, value):
            nonlocal calls
            calls += 1
            self.memory.write(address, b"?"*len(value) if calls == 1 else value)
        with self.assertRaisesRegex(Rejected, "previous bytes restored"):
            apply_transaction(self.memory.read, write, self.plan())
        self.assertEqual(self.memory.data, self.original)

    def test_rollback_failure_is_explicit_and_other_rollbacks_continue(self):
        calls = 0
        def write(address, value):
            nonlocal calls
            calls += 1
            if calls in (2, 3):
                raise OSError("simulated failure")
            self.memory.write(address, value)
        with self.assertRaisesRegex(Rejected, "ROLLBACK INCOMPLETE"):
            apply_transaction(self.memory.read, write, self.plan())
        self.assertEqual(calls, 4)

    def test_interrupt_also_rolls_back(self):
        calls = 0
        def write(address, value):
            nonlocal calls
            calls += 1
            self.memory.write(address, value)
            if calls == 1:
                raise KeyboardInterrupt()
        with self.assertRaisesRegex(Rejected, "previous bytes restored"):
            apply_transaction(self.memory.read, write, self.plan())
        self.assertEqual(self.memory.data, self.original)


def menu_observation():
    return {"stage_field_candidate": 1102,
            "session": {"root_stable": True, "fields": {"session_type_candidate": 4},
                        "slots": [{"slot_state": 0} for _ in range(8)]},
            "player_objects": {"root_stable": True, "entry_present": [False]*8}}


class StateGuardTests(unittest.TestCase):
    def test_observed_menu_shapes_allowed(self):
        for session_type in (0, 4):
            observation = menu_observation()
            observation["session"]["fields"]["session_type_candidate"] = session_type
            require_idle_menu(observation)

    def test_host_join_gameplay_and_unreadable_state_refused(self):
        for mutation in (
                lambda o: o.update(stage_field_candidate=1212),
                lambda o: o["session"]["fields"].update(session_type_candidate=1),
                lambda o: o["session"]["fields"].update(session_type_candidate=2),
                lambda o: o["session"].update(root_stable=False),
                lambda o: o["player_objects"].update(entry_present=[True] + [False]*7),
                lambda o: o["player_objects"].update(entry_present=None),
                lambda o: o["session"]["slots"][1].update(slot_state=1)):
            observation = menu_observation()
            mutation(observation)
            with self.assertRaises(Rejected):
                require_idle_menu(observation)

    def test_zero_manager_exception_is_explicit_not_general_unknown(self):
        observation = menu_observation()
        observation["player_objects"] = {"root_stable": None, "entry_present": None}
        with self.assertRaises(Rejected):
            require_idle_menu(observation)
        require_idle_menu(observation, manager_absent=True)

    def test_six_slot_assessment_requires_all_distinct_indices_and_no_objects(self):
        observation = {"session": {"root_stable": True,
                       "fields": {"session_type_candidate": 1, "create_capacity_candidate": 6},
                       "slots": [{"slot_kind": 3 if i == 0 else 1 if i < 6 else 0,
                                  "slot_state": 1 if i == 0 else 0,
                                  "randomized_slot": 5-i if i < 6 else 0}
                                 for i in range(8)]},
                       "player_objects": {"root_stable": True, "entry_present": [False]*8},
                       "native_sites": [{"matches_candidate": True, "legacy_site_matches_disk": True}]*3}
        self.assertTrue(lobby_assessment(observation).startswith("SIX-SLOT"))
        for mutation in (
                lambda o: o["session"]["fields"].update(create_capacity_candidate=7),
                lambda o: o["session"]["slots"][2].update(randomized_slot=5),
                lambda o: o["native_sites"][0].update(matches_candidate=False),
                lambda o: o["native_sites"][0].update(legacy_site_matches_disk=False),
                lambda o: o.update(native_sites=[]),
                lambda o: o["player_objects"].update(entry_present=[True] + [False]*7)):
            trial = copy.deepcopy(observation)
            mutation(trial)
            self.assertFalse(lobby_assessment(trial).startswith("SIX-SLOT"))


class BackendControlTests(unittest.TestCase):
    def process(self, suspend=0, resume=0):
        events = []
        class NT:
            def NtSuspendProcess(self, handle):
                events.append("suspend")
                return suspend
            def NtResumeProcess(self, handle):
                events.append("resume")
                return resume
        process = object.__new__(WindowsTrialProcess)
        process.handle, process.nt, process.is_suspended = 1, NT(), False
        return process, events

    def test_resumes_on_guard_or_transaction_error(self):
        process, events = self.process()
        with self.assertRaises(ValueError):
            with process.suspended():
                self.assertTrue(process.is_suspended)
                raise ValueError("simulated validation failure")
        self.assertEqual(events, ["suspend", "resume"])
        self.assertFalse(process.is_suspended)

    def test_failed_suspend_or_resume_not_silently_accepted(self):
        process, events = self.process(suspend=-1)
        with self.assertRaisesRegex(Rejected, "suspension failed"):
            with process.suspended():
                self.fail("entered after suspend failed")
        self.assertEqual(events, ["suspend"])
        process, events = self.process(resume=-1)
        with self.assertRaisesRegex(Rejected, "Could not resume"):
            with process.suspended():
                pass
        self.assertEqual(events, ["suspend", "resume"])

    def test_write_requires_suspension(self):
        process, _ = self.process()
        with self.assertRaisesRegex(Rejected, "while game threads"):
            process.write_code(0x400000, b"abc")

    def test_writer_restores_protection_and_flushes_instruction_cache(self):
        events = []
        class API:
            def VirtualProtectEx(self, handle, address, size, protection, previous):
                previous._obj.value = 0x20
                events.append(("protect", protection))
                return True
            def WriteProcessMemory(self, handle, address, data, size, copied):
                copied._obj.value = size
                events.append(("write", ctypes.string_at(data, size)))
                return True
            def FlushInstructionCache(self, handle, address, size):
                events.append(("flush", size))
                return True
        process, _ = self.process()
        process.api, process.is_suspended, process.protection_failed = API(), True, False
        process.write_code(0x400000, b"abc")
        self.assertEqual(events, [("protect", 0x40), ("write", b"abc"), ("flush", 3), ("protect", 0x20)])


if __name__ == "__main__":
    unittest.main()
