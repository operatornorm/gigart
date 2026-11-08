"""Bundle an explicit source/helper allowlist for the native-Steam Proton preview."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from steam_patch import VERSION, pinned_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper", type=Path, required=True)
    args = parser.parse_args()
    pinned_manifest()
    helper = args.helper.read_bytes()
    assert helper[:2] == b"MZ"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    files = {name: (ROOT / name).read_bytes() for name in (
        "run-proton.sh", "proton_launcher.py", "proton_support.py", "steam_patch.py",
        "backend_check.py", "menu_state.py", "native_trial.py", "patch_candidate.py",
        "probe_windows.py", "session_probe.py", "candidate.json", "docs/tested-build.json",
        "docs/tested-steam-build.json")}
    files["RE6MercenariesPatch.exe"] = helper
    files["README.txt"] = (ROOT / "docs/PROTON-QUICKSTART.txt").read_bytes()
    files["proton-bundle.json"] = (json.dumps({"version": VERSION, "source_commit": commit,
                                             "helper_sha256": hashlib.sha256(helper).hexdigest(),
                                             "status": "Proton preview; no live RE6/Proton result yet"}, indent=2) + "\n").encode()
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    name = f"RE6MercenariesPatch-{VERSION}-linux-proton"
    archive = output / f"{name}.tar.gz"
    with tarfile.open(archive, "x:gz") as bundle:
        for relative, data in files.items():
            entry = tarfile.TarInfo(f"{name}/{relative}")
            entry.size = len(data)
            entry.mode = 0o755 if relative == "run-proton.sh" else 0o644
            bundle.addfile(entry, io.BytesIO(data))
    (output / "PROTON-SHA256SUMS.txt").write_text(
        f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
