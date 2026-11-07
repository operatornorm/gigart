"""Read bounded lobby fields; these observations never establish human-client QA."""
import struct


# Offsets belong only to the SHA-256-pinned image in candidate.json.
# Native evidence and the distinction between six admission slots and eight
# stored entries are recorded in docs/SESSION-ADMISSION.md.
STORED_SLOTS = 8
ADMISSION_SLOTS = 6
SCALARS = {
    "mode": 0xAC,
    "session_type_candidate": 0x74,
    "stage_index_candidate": 0x3E50,
    "create_capacity_candidate": 0x3E54,
    "timer_state_candidate": 0x4864,
    "timer_slot_mask_candidate": 0x4868,
}
ARRAYS = {
    "slot_state": 0x3EFC,
    "slot_kind": 0x3F1C,
    "randomized_slot": 0x3F3C,
}


def read_u32(read, address):
    data = read(address, 4)
    return struct.unpack("<I", data)[0] if data is not None and len(data) == 4 else None


def summarize_slots(slots):
    """Apply the predicates in native 0x5515a0 and 0x551500, without names/IDs."""
    rows = slots[:ADMISSION_SLOTS]
    complete = len(rows) == ADMISSION_SLOTS and all(
        row["slot_kind"] is not None and row["slot_state"] is not None for row in rows)
    # A partial read must not silently count as a free or empty slot.
    if not complete:
        return {"admission_fields_complete": False,
                "free_kind_1_indices": None, "free_kind_2_indices": None,
                "native_counted_slot_indices": None}
    return {
        "admission_fields_complete": True,
        "free_kind_1_indices": [i for i, row in enumerate(rows)
                                if row["slot_kind"] == 1 and row["slot_state"] == 0],
        "free_kind_2_indices": [i for i, row in enumerate(rows)
                                if row["slot_kind"] == 2 and row["slot_state"] == 0],
        "native_counted_slot_indices": [i for i, row in enumerate(rows)
                                        if row["slot_kind"] != 0 and row["slot_state"] not in (0, 3)],
    }


def session_snapshot(read, base, root_rva):
    root_address = base + root_rva
    root = read_u32(read, root_address)
    result = {"schema": 1, "status": "UNKNOWN", "gameplay_validated": False,
              "atomic_snapshot": False, "root_stable": None,
              "fields": None, "slots": None, "summary": None}
    if root is None or not 0x10000 <= root <= 0xFFF00000:
        return result
    fields = {name: read_u32(read, root + offset) for name, offset in SCALARS.items()}
    slots = [{"index": i, **{name: read_u32(read, root + offset + 4*i)
                             for name, offset in ARRAYS.items()}}
             for i in range(STORED_SLOTS)]
    # Discard a sample if the global object changed while reading. This does
    # not make unchanged-root reads atomic, or prevent changes within the object.
    after = read_u32(read, root_address)
    if after != root:
        result["status"] = "ROOT CHANGED OR BECAME UNREADABLE; SAMPLE DISCARDED"
        result["root_stable"] = False if after is not None else None
        return result
    result.update(status="OBSERVATIONS ONLY; NO CLIENT OR SPAWN VALIDATION",
                  root_stable=True, fields=fields, slots=slots,
                  summary=summarize_slots(slots))
    return result


def player_objects_snapshot(read, base, root_rva):
    """Observe sPlayer's pointer table, without dereferencing player objects."""
    address = base + root_rva
    root = read_u32(read, address)
    result = {"status": "UNKNOWN", "root_stable": None,
              "entry_present": None, "distinct_non_null_entries": None,
              "duplicate_entry_indices": None, "gameplay_validated": False,
              "atomic_snapshot": False}
    if root is None or not 0x10000 <= root <= 0xFFF00000:
        return result
    # Native getter 0x590b00 accepts only indices 0..7 and reads +0x24 + 4*i.
    pointers = [read_u32(read, root + 0x24 + 4*i) for i in range(STORED_SLOTS)]
    after = read_u32(read, address)
    if after != root:
        result["status"] = "ROOT CHANGED OR BECAME UNREADABLE; SAMPLE DISCARDED"
        result["root_stable"] = False if after is not None else None
        return result
    # Invalid nonzero values remain unknown, rather than apparent player objects.
    pointers = [p if p == 0 or p is not None and 0x10000 <= p <= 0xFFF00000 else None
                for p in pointers]
    present = [None if p is None else p != 0 for p in pointers]
    complete = all(p is not None for p in pointers)
    non_null = [p for p in pointers if p]
    result.update(status="POINTER TABLE ONLY; NO ALIVE, CONTROL OR CLIENT VALIDATION",
                  root_stable=True, entry_present=present,
                  distinct_non_null_entries=len(set(non_null)) if complete else None,
                  duplicate_entry_indices=[i for i, p in enumerate(pointers)
                                           if p and pointers.count(p) > 1] if complete else None)
    return result
