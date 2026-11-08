#!/bin/sh
set -eu
bundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'Python 3.10 or later is required for this Linux launcher.' >&2
    exit 1
fi
exec python3 "$bundle_dir/proton_launcher.py" "$@"
