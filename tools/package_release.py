"""Package an explicit allowlist; never include private reports or game inputs."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from steam_patch import VERSION, pinned_manifest


def main():
    pinned_manifest()
    output = ROOT / "dist"
    executable = output / "RE6MercenariesPatch.exe"
    if not executable.is_file():
        raise SystemExit("Build the Windows executable first.")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    metadata = json.dumps({"version": VERSION, "source_commit": commit,
                           "tested_patch_source": "v0.1.0-tested"}, indent=2) + "\n"
    archive = output / f"RE6MercenariesPatch-{VERSION}-windows-x64.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(executable, executable.name)
        bundle.write(ROOT / "docs/STEAM-QUICKSTART.txt", "README.txt")
        bundle.write(ROOT / "docs/tested-build.json", "tested-build.json")
        bundle.writestr("BUILD-INFO.json", metadata)
    sums = []
    for path in (archive, executable):
        sums.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")
    (output / "SHA256SUMS.txt").write_text("".join(sums), encoding="utf-8")


if __name__ == "__main__":
    main()
