"""CI check of the packaged helper in Wine; no Steam installation or game used."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from proton_launcher import wine_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args()
    helper, fixture = args.helper.resolve(strict=True), args.fixture.resolve(strict=True)
    # Synthetic native-Steam library to exercise Wine path and manifest discovery.
    library = helper.parent / "Steam library with spaces"
    game = library / "steamapps/common/Resident Evil 6/BH6.exe"
    game.parent.mkdir(parents=True)
    game.touch()
    (library / "steamapps/appmanifest_221040.acf").write_text(
        '"AppState" { "appid" "221040" "installdir" "Resident Evil 6" }')
    command = ["wine", str(helper)]
    startup = helper.parent / "startup-result.json"
    result = subprocess.run(command + ["--self-test", "--proton-library", wine_path(library),
                                      "--self-test-report", "Z:" + str(startup).replace("/", "\\")], timeout=90)
    if result.returncode:
        raise RuntimeError(startup.read_text() if startup.exists() else "Wine helper startup failed before reporting.")
    # Map the same native library through a second Wine drive to reproduce the
    # differing path spellings used by a game and an external helper.
    drive = Path(os.environ["WINEPREFIX"]) / "dosdevices/q:"
    drive.symlink_to(library, target_is_directory=True)
    unrelated = helper.parent / "Separate BH6.exe"
    unrelated.write_bytes(game.read_bytes())  # Same bytes, distinct file identity.
    alias_report = helper.parent / "alias-result.json"
    result = subprocess.run(command + ["--self-test", "--proton-library", wine_path(library),
                                      "--self-test-image-alias", r"Q:\steamapps\common\Resident Evil 6\BH6.exe",
                                      "--self-test-unregistered-image", wine_path(unrelated),
                                      "--self-test-report", "Z:" + str(alias_report).replace("/", "\\")], timeout=90)
    if result.returncode:
        raise RuntimeError(alias_report.read_text() if alias_report.exists() else "Wine drive alias check failed.")
    report = helper.parent / "backend-result.json"
    process = subprocess.run(command + ["--backend-self-test", wine_path(fixture),
                                       "--self-test-report", "Z:" + str(report).replace("/", "\\")],
                             timeout=90)
    result = json.loads(report.read_text())
    print(json.dumps(result, indent=2), flush=True)
    assert process.returncode == 0, result
    assert result["success"] and result["helper_pointer_bits"] == 64, result


if __name__ == "__main__":
    main()
