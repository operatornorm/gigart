"""Start the patch helper in app 221040's existing Proton prefix using Protontricks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from patch_candidate import ROOT, Rejected, candidate_bytes
from steam_patch import discover_installs, pinned_manifest


def native_steam_roots(home, environ):
    roots = []
    for name in ("STEAM_DIR", "STEAM_COMPAT_CLIENT_INSTALL_PATH"):
        if environ.get(name):
            roots.append(Path(environ[name]))
    roots.extend([Path(environ.get("XDG_DATA_HOME", str(home / ".local/share"))) / "Steam",
                  home / ".steam/steam", home / ".steam/root"])
    return list(dict.fromkeys(path.resolve() for path in roots if path.is_dir()))


def wine_path(path):
    path = Path(path).resolve(strict=True)
    if "\\" in str(path):
        raise Rejected("Backslashes in Linux paths are unsupported by this Proton preview.")
    # Valve's Proton setup_prefix creates dosdevices/z: -> /.
    return "Z:" + str(path).replace("/", "\\")


def build_command(roots, bundle, environ, launch_program):
    spec = pinned_manifest()
    installs = discover_installs(roots)
    if len(installs) != 1:
        raise Rejected("Find exactly one installed RE6 copy. Use --steam-dir for its native Steam library.")
    executable = installs[0]
    candidate_bytes(executable.read_bytes(), spec)
    library = executable.parents[3]
    compat = Path(environ.get("STEAM_COMPAT_DATA_PATH", str(library / "steamapps/compatdata/221040")))
    if not (compat / "pfx/system.reg").is_file():
        raise Rejected("RE6's Proton prefix is missing. Start RE6 from Steam with Proton first.")
    metadata = json.loads((bundle / "proton-bundle.json").read_text(encoding="utf-8"))
    helper = bundle / "RE6MercenariesPatch.exe"
    if hashlib.sha256(helper.read_bytes()).hexdigest() != metadata["helper_sha256"]:
        raise Rejected("Bundled helper checksum differs. Extract a fresh release download.")
    command = [str(launch_program), "--appid", "221040", str(helper),
               "--proton-library", wine_path(library)]
    return command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steam-dir", type=Path, help="Optional native Steam root/library path.")
    parser.add_argument("--dry-run", action="store_true", help="Validate paths and print the launch command without running it.")
    args = parser.parse_args()
    try:
        if not sys.platform.startswith("linux"):
            raise Rejected("This entry point is for desktop Linux with native Steam.")
        program = shutil.which("protontricks-launch")
        if program is None:
            raise Rejected("Install native Protontricks (including protontricks-launch), then retry. "
                           "Instructions: https://github.com/Matoking/protontricks#installation")
        launch_environ = dict(os.environ)
        if args.steam_dir:
            launch_environ["STEAM_DIR"] = str(args.steam_dir.resolve(strict=True))
        roots = [args.steam_dir] if args.steam_dir else native_steam_roots(Path.home(), launch_environ)
        command = build_command(roots, ROOT, launch_environ, program)
        if args.dry_run:
            print(shlex.join(command))
            return
        # Argument list only: paths and metacharacters are never shell code.
        result = subprocess.run(command, env=launch_environ, check=False)
        if result.returncode:
            raise Rejected(f"Protontricks exited with code {result.returncode}. "
                           "Start RE6 using the same Proton version, then retry.")
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Proton launcher stopped: {exc}\n")


if __name__ == "__main__":
    main()
