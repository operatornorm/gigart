import struct
import unittest

from session_probe import ARRAYS, SCALARS, player_objects_snapshot, session_snapshot, summarize_slots


class SessionProbeTests(unittest.TestCase):
    def setUp(self):
        self.base, self.root_rva, self.root = 0x400000, 0x13CF454, 0x20000000
        self.memory = {self.base + self.root_rva: struct.pack("<I", self.root)}

    def put(self, offset, value):
        self.memory[self.root + offset] = struct.pack("<I", value)

    def capture(self, reader=None):
        return session_snapshot(reader or (lambda address, size: self.memory.get(address)),
                                self.base, self.root_rva)

    def fill(self, kinds, states):
        for i in range(8):
            self.put(ARRAYS["slot_kind"] + 4*i, kinds[i])
            self.put(ARRAYS["slot_state"] + 4*i, states[i])
            self.put(ARRAYS["randomized_slot"] + 4*i, 7-i)

    def test_reads_all_eight_but_admits_only_first_six(self):
        self.fill([3, 1, 1, 2, 1, 0, 1, 2], [1, 1, 0, 0, 3, 0, 0, 0])
        for offset in SCALARS.values():
            self.put(offset, 0)
        self.put(SCALARS["mode"], 80)
        result = self.capture()
        self.assertEqual(len(result["slots"]), 8)
        self.assertEqual(result["fields"]["mode"], 80)
        self.assertEqual(result["summary"]["free_kind_1_indices"], [2])
        self.assertEqual(result["summary"]["free_kind_2_indices"], [3])
        self.assertEqual(result["summary"]["native_counted_slot_indices"], [0, 1])

    def test_capacity_and_randomization_do_not_count_as_clients(self):
        self.fill([3, 1, 1, 1, 1, 1, 0, 0], [1, 0, 0, 0, 0, 0, 0, 0])
        self.put(SCALARS["create_capacity_candidate"], 6)
        result = self.capture()
        self.assertEqual(result["summary"]["native_counted_slot_indices"], [0])
        self.assertFalse(result["gameplay_validated"])
        self.assertNotIn("human_clients", result)

    def test_four_counted_slots_still_do_not_prove_spawns_or_clients(self):
        self.fill([3, 1, 1, 1, 1, 1, 0, 0], [1, 1, 1, 1, 0, 0, 0, 0])
        result = self.capture()
        self.assertEqual(result["summary"]["native_counted_slot_indices"], [0, 1, 2, 3])
        self.assertFalse(result["gameplay_validated"])
        self.assertFalse(result["atomic_snapshot"])

    def test_partial_read_is_unknown_not_an_empty_slot(self):
        self.fill([1]*8, [0]*8)
        del self.memory[self.root + ARRAYS["slot_state"] + 8]
        result = self.capture()
        self.assertIsNone(result["slots"][2]["slot_state"])
        self.assertFalse(result["summary"]["admission_fields_complete"])
        self.assertIsNone(result["summary"]["free_kind_1_indices"])

    def test_unreadable_tail_does_not_invalidate_six_slot_predicate(self):
        self.fill([1]*8, [0]*8)
        del self.memory[self.root + ARRAYS["slot_state"] + 28]
        result = self.capture()
        self.assertTrue(result["summary"]["admission_fields_complete"])
        self.assertEqual(result["summary"]["free_kind_1_indices"], list(range(6)))

    def test_bad_roots_do_not_trigger_object_reads(self):
        for value in (None, 0, 0xFFFF, 0xFFF00001):
            calls = []
            def read(address, size):
                calls.append(address)
                return None if value is None else struct.pack("<I", value)
            result = self.capture(read)
            self.assertEqual(calls, [self.base + self.root_rva])
            self.assertIsNone(result["slots"])

    def test_root_change_discards_incoherent_sample(self):
        reads = 0
        def read(address, size):
            nonlocal reads
            if address == self.base + self.root_rva:
                reads += 1
                return struct.pack("<I", self.root if reads == 1 else self.root + 0x10000)
            return b"\0"*4
        result = self.capture(read)
        self.assertFalse(result["root_stable"])
        self.assertIsNone(result["slots"])
        self.assertIsNone(result["summary"])

    def test_short_reads_and_lost_root_are_unknown(self):
        result = self.capture(lambda address, size: b"\0")
        self.assertIsNone(result["slots"])
        root_reads = 0
        def read(address, size):
            nonlocal root_reads
            if address == self.base + self.root_rva:
                root_reads += 1
                return struct.pack("<I", self.root) if root_reads == 1 else None
            return b"\0"
        result = self.capture(read)
        self.assertIsNone(result["root_stable"])
        self.assertIsNone(result["summary"])

    def test_native_count_predicate_is_not_only_state_one(self):
        rows = [{"slot_kind": k, "slot_state": s} for k, s in
                [(0, 1), (1, 0), (1, 1), (2, 2), (3, 3), (1, 4)]]
        self.assertEqual(summarize_slots(rows)["native_counted_slot_indices"], [2, 3, 5])


class PlayerObjectTests(unittest.TestCase):
    def capture(self, values, change_root=False):
        root, base, rva = 0x30000000, 0x400000, 0x13D0468
        root_reads = 0
        addresses = []
        def read(address, size):
            nonlocal root_reads
            addresses.append((address, size))
            if address == base + rva:
                root_reads += 1
                value = root + 0x10000 if change_root and root_reads == 2 else root
            else:
                index = (address - root - 0x24)//4
                self.assertIn(index, range(8))
                value = values[index]
            return None if value is None else struct.pack("<I", value)
        result = player_objects_snapshot(read, base, rva)
        self.assertTrue(all(size == 4 for _, size in addresses))
        self.assertEqual(len(addresses), 10)
        return result

    def test_object_presence_is_separate_from_client_and_alive_proof(self):
        result = self.capture([0x40000000 + 0x1000*i for i in range(4)] + [0]*4)
        self.assertEqual(result["entry_present"], [True]*4 + [False]*4)
        self.assertEqual(result["distinct_non_null_entries"], 4)
        self.assertFalse(result["gameplay_validated"])

    def test_duplicate_objects_are_not_distinct_players(self):
        result = self.capture([0x40000000]*4 + [0]*4)
        self.assertEqual(result["distinct_non_null_entries"], 1)
        self.assertEqual(result["duplicate_entry_indices"], [0, 1, 2, 3])

    def test_unreadable_and_invalid_entries_remain_unknown(self):
        result = self.capture([0, None, 0x10, 0xFFFFFFFF, 0, 0, 0, 0])
        self.assertEqual(result["entry_present"][:4], [False, None, None, None])
        self.assertIsNone(result["distinct_non_null_entries"])

    def test_changed_manager_does_not_mix_tables(self):
        result = self.capture([0]*8, change_root=True)
        self.assertFalse(result["root_stable"])
        self.assertIsNone(result["entry_present"])

    def test_missing_manager_is_unknown_not_zero_players(self):
        for value in (None, 0, 0x10, 0xFFFFFFFF):
            result = player_objects_snapshot(lambda a, s: None if value is None else struct.pack("<I", value),
                                             0x400000, 0x13D0468)
            self.assertIsNone(result["entry_present"])
            self.assertIsNone(result["distinct_non_null_entries"])


if __name__ == "__main__":
    unittest.main()
