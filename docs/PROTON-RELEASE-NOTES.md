First **desktop Linux / native Steam Proton preview**. The confirmed Windows
[`v0.2.2`](https://github.com/operatornorm/gigart/releases/tag/v0.2.2) release is
preserved unchanged, with its source and binary checksums recorded in the repo.

The Linux entry point detects the native Steam library, checks the original
RE6 executable, and uses **Protontricks app 221040** to start the helper in RE6's
existing Proton environment. The exact three patch records and four original
runtime modules are unchanged. No scene/menu ID is required; inactive-session,
code identity, suspension, readback and rollback checks remain required.

Extract the entire Linux archive, start RE6 normally under Proton outside a
lobby/round, then run `bash ./run-proton.sh` from the extracted folder. Click
**Refresh → Apply**. Requires native Steam, Python 3.10+ and native Protontricks.
Full setup and a first-trial procedure are in the archive's `README.txt`.

Automated checks build the Windows helper and check its GUI, Linux library/path
handling, and Wine access to an owned **32-bit synthetic process from a 64-bit
helper**: suspend, write a read-only page, read back, restore original bytes and
page protection, then resume. These checks do not run RE6, Steam or Valve Proton.
This release has **no live RE6/Proton confirmation yet** and is a prerelease.

For the first trial, collect diagnostics after Apply and in a fresh empty
Mercenaries lobby; no other people or round are needed. The original Windows
three-player report remains separate from Proton compatibility testing.

The first preview targets x86-64 desktop Linux with native Steam and a normal
64-bit Proton prefix. Flatpak Steam/Protontricks, Deck Gaming Mode and custom
pure-32-bit prefixes are outside this trial. No game binaries/assets are included.
