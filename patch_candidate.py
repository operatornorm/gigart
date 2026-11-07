"""Inspect or build an offline native-code candidate. Never launches the game."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent


class Rejected(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_manifest():
    return json.loads((ROOT / "candidate.json").read_text())


def inspect_bytes(data, spec):
    if len(data) != spec["size_bytes"] or digest(data) != spec["input_sha256"]:
        raise Rejected("Unsupported executable: exact input size/SHA-256 required.")
    try:
        pe = struct.unpack_from("<I", data, 0x3C)[0]
        if data[:2] != b"MZ" or data[pe:pe + 4] != b"PE\0\0":
            raise Rejected("Invalid PE image.")
        machine, count = struct.unpack_from("<HH", data, pe + 4)
        optional_size = struct.unpack_from("<H", data, pe + 20)[0]
        magic = struct.unpack_from("<H", data, pe + 24)[0]
        image_base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
        if machine != spec["machine"] or magic != 0x10B or image_base != spec["image_base"]:
            raise Rejected("Unexpected PE architecture or image base.")
        sections = [struct.unpack_from("<IIII", data, pe + 24 + optional_size + 40*i + 8)
                    for i in range(count)]
    except struct.error as exc:
        raise Rejected("Truncated PE headers.") from exc
    regions = []
    for patch in spec["patches"]:
        start = patch["file_offset"]
        before = bytes.fromhex(patch["expected_hex"])
        after = bytes.fromhex(patch["replacement_hex"])
        end = start + len(before)
        if not before or len(before) != len(after) or start < 0 or end > len(data):
            raise Rejected("Invalid patch range or length.")
        mappings = [raw + patch["rva"] - rva for _, rva, size, raw in sections
                    if rva <= patch["rva"] and patch["rva"] + len(before) <= rva + size]
        if mappings != [start]:
            raise Rejected("RVA/file-offset mapping is not unique and consistent.")
        if any(start < z and a < end for a, z in regions):
            raise Rejected("Overlapping patch sites.")
        regions.append((start, end))
        context_start = patch["context_offset"]
        context = bytes.fromhex(patch["context_hex"])
        if context_start < 0 or context_start + len(context) > len(data):
            raise Rejected("Invalid surrounding-code guard.")
        if data[context_start:context_start + len(context)] != context:
            raise Rejected("Surrounding instructions do not match.")
        if data[start:end] != before:
            raise Rejected("Original instructions do not match.")
    return {"input_sha256": digest(data), "patch_sites_verified": len(regions),
            "status": "STATIC CHECK ONLY", "gameplay_validated": False}


def candidate_bytes(data, spec):
    inspect_bytes(data, spec)
    result = bytearray(data)
    for patch in spec["patches"]:
        value = bytes.fromhex(patch["replacement_hex"])
        start = patch["file_offset"]
        result[start:start + len(value)] = value
    result = bytes(result)
    if digest(result) != spec["candidate_sha256"]:
        raise Rejected("Candidate output checksum mismatch.")
    return result


def write_candidate(source, spec, workspace=ROOT):
    source = Path(source).resolve(strict=True)
    output = Path(workspace).resolve() / "private" / "BH6.native-candidate.exe"
    if output.resolve() == source:
        raise Rejected("Input and output must differ.")
    result = candidate_bytes(source.read_bytes(), spec)
    output.parent.mkdir(parents=True, exist_ok=True)
    # A symlinked private directory must not redirect output outside the workspace.
    if not output.resolve().is_relative_to(Path(workspace).resolve()):
        raise Rejected("Output escapes the project workspace.")
    with output.open("xb") as stream:
        stream.write(result)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--build-native-candidate", action="store_true",
                        help="Write the incomplete offline candidate under private/.")
    args = parser.parse_args()
    try:
        spec = load_manifest()
        report = inspect_bytes(args.executable.read_bytes(), spec)
        if args.build_native_candidate:
            path = write_candidate(args.executable, spec)
            report["candidate_file"] = path.name
            report["candidate_sha256"] = spec["candidate_sha256"]
        print(json.dumps(report, indent=2))
    except (OSError, Rejected, ValueError) as exc:
        parser.exit(1, f"Refused: {exc}\n")


if __name__ == "__main__":
    main()
