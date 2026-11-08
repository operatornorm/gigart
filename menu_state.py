"""Read the selected scene record using the pinned game's native getter layout."""
from session_probe import read_u32

# Native getter 0x455380: [info + 0x412a4 + [info + 0x20] * 0x3ce4].
# Constructor 0x5682a8..0x5682c1 constructs four records. See docs/MENU-STATE.md.
RECORD_INDEX_OFFSET = 0x20
RECORD_STRIDE = 0x3CE4
RECORD_COUNT = 4


def selected_scene(read, base, spec):
    root_address = base + spec["probe_candidates"]["game_info_root_rva"]
    root = read_u32(read, root_address)
    result = {"root_stable": None, "record_index": None,
              "record_index_stable": None, "stage": None,
              "record_zero_stage": None, "atomic_snapshot": False}
    if root is None or not 0x10000 <= root <= 0xFFF00000:
        return result
    index = read_u32(read, root + RECORD_INDEX_OFFSET)
    result["record_index"] = index
    # Never treat an unreadable/out-of-range index as record zero.
    if index is None or not 0 <= index < RECORD_COUNT:
        return result
    offset = spec["probe_candidates"]["stage_field_offset"]
    zero = read_u32(read, root + offset)
    stage = read_u32(read, root + offset + index * RECORD_STRIDE)
    index_after = read_u32(read, root + RECORD_INDEX_OFFSET)
    root_after = read_u32(read, root_address)
    result["root_stable"] = root_after == root if root_after is not None else None
    result["record_index_stable"] = index_after == index if index_after is not None else None
    if result["root_stable"] is True and result["record_index_stable"] is True:
        result.update(stage=stage, record_zero_stage=zero)
    return result
