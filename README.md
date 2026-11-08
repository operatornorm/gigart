# RE6 v1.1.0 Mercenaries patch

**Three-player standard Mercenaries and No Mercy gameplay has been reported
working by the host and two friends.** They reported no identifiable problems
with the timer, score, items or enemy spawns. Supplied host captures separately
verify admission progressing from two occupied slots to three with the exact
patch bytes active. Four or more real players and every map remain unverified.

The exact source kit used for those sessions is frozen at
[`v0.1.0-tested`](https://github.com/operatornorm/gigart/tree/v0.1.0-tested)
(commit `ea19adebe0d2151fe81868f211ce8b9821d5c22b`). The four runtime modules
and all three patch records remain byte-for-byte identical to that kit; their
hashes and the target identity are recorded in [tested-build.json](docs/tested-build.json).
See [the evidence and its limits](docs/THREE-PLAYER-RESULT.md).

This repository contains source tools and a patch description, without the game
executable, assets or Fluffy's software. The patch writes only the running game's
three code spans. It does not change the game executable on disk, timer, mode,
Steam checks or saves. Closing RE6 removes the memory changes.

## Original test kit

The original `native_trial.py` tool is preserved unchanged. It requires an
isolated game copy and an explicit process ID for writes. Its historical
[lobby trial instructions](docs/LOBBY-TRIAL.md) and
[three-client joining plan](docs/THREE-CLIENT-ADMISSION.md) describe the experiments
leading to the result above. They are not additional tests required to establish
the reported three-player success.

The ordinary `probe_windows.py` collector requests read-only access only.

## Current evidence

The privately supplied BH6.exe has file/product version **1.1.0.0**, PE32/x86,
preferred base 0x400000, image size 21671936 and SHA-256:

`b8bceaf09272d5f30b89940737763afa6dfb78647c81165af1aa8a10d0afeb35`

This identifies the exact supplied build, not every regional or modified 1.1.0
executable. Original bytes at the candidate sites are still the two-player code.

Fluffy's official manager v3.084 was inspected without executing it. Its Host
6-player control prepares three code changes. Strong matches in this game image:

| Purpose inferred from native code | Legacy RVA | Matched v1.1.0 RVA |
|---|---|---|
| Create-session capacity calculation | 0x60f51d | 0x612cdd |
| Slot-count initialization | 0x60d361 | 0x610b21 |
| Randomized slot assignment / occupied-slot mask | 0x60d37a | 0x610b3a |

All three have a 0x37c0 difference, but the matches were checked against actual
instructions and surrounding control flow, not accepted from that difference
alone. The old locations contain unrelated instructions in this image.

The recurring trainer poke was traced to the message `Timer frozen.` and a
120.0f freeze record. It is not a mode-selection write. The old tool derives its
timer address from a cached game-info pointer minus 0x794. The current root RVA
0x13cf49c is supported by the game's native references and the separately read
[RE6 autosplitter](https://github.com/TheDementedSalad/RE6-Autosplitter/blob/main/Resident%20Evil%206%20Autosplitter.asl),
which distinguishes English 1.0.6 and 1.1.0 and gives this build's image size.
A subsequent solo No Mercy capture corroborates this displacement in that
session. The mode-object timer is now the better-grounded address derivation;
heap adjacency is never assumed. Nothing in this kit writes to either field.

Further static tracing found a float countdown at mode-object +0x486c: the
function at game VA 0x55a610 subtracts frame time and stores the result; the
function at VA 0x5585f0 adds bonus time. Initialization at VA 0x55cd44 stores the
return value of VA 0x551180 there. The collector now reads that field directly
from the mode root, its adjacent elapsed-time/state candidates, and the older
game-info-relative candidate independently. It never assumes that two heap
objects are adjacent. These instructions and the subsequent clock-correlated capture identify a live
countdown field for that solo No Mercy session. Multiplayer write/freeze behavior
and other maps remain untested.

## Read-only Windows collector

Requires Python 3.10 or later; no pip packages. Extract this kit into a separate
workspace outside the game installation. With your existing game process already
running, find its process ID in PowerShell:

```powershell
Get-Process BH6 | Select-Object Id
```

From the kit's directory, substitute that number below:

```powershell
py -3 .\probe_windows.py --pid 1234
```

The collector requests read/query access only. It checks the executable's exact
hash and module size, then records six snapshots in `private/probe-*.json`:

- Original/candidate bytes at the three relocated code sites.
- Whether the old trainer's three historical target locations still match disk.
- Candidate game-info, mode, stage and timer values; unreadable values remain null.
- A separate native timer/elapsed/state path through the mode object, and whether
  both timer candidates currently resolve to the same address.

It does not send game input, patch memory, change protection, create threads in
the game, edit files in the game installation, access saves or operate an account.
It writes only its JSON report inside this kit's private workspace. Share that
report privately for the next analysis step. This is diagnostic observation,
not a human playtest or a multiplayer PASS.

### Captured No Mercy baseline

The first six-sample capture was made at the main/menu screen. All three
relocated sites matched original code; all three historical locations matched
disk during those samples. Mode and timer candidates were zero.

A subsequent capture labelled `no-mercy-running` recorded twenty samples over
19.012 seconds. The visible clock and Urban Chaos map were independently
confirmed by the person collecting it:

| Observation | Result |
|---|---|
| Mode field | 80 (0x50), in the confirmed No Mercy session |
| Stage field | 1212, matching Urban Chaos |
| Native countdown | 52.47375 to 33.47399 seconds |
| Elapsed field | Increased by 19.00409 seconds |
| Timer paths | Equal values and addresses in all twenty samples |
| Three native code spans | Original code throughout |
| Three historical trainer locations | Matched disk throughout |

The countdown fell 18.99976 seconds in 19.012 wall-clock seconds. This confirms
timer observation on that map/session; it is not a memory-write, lobby-capacity,
four-client or all-map test. Raw reports and heap addresses remain private.
No further capture is required to repeat this timer-identification step.

The collector can label captures with `--context no-mercy-running`, collect a
longer window with `--samples 20`, and wait for game focus to return with
`--delay 10`. Labels remain user-reported context rather than automatic proof.

## Offline native candidate

`patch_candidate.py` defaults to inspection only:

```powershell
py -3 .\patch_candidate.py "<test copy>\BH6.exe"
```

For analysis, `--build-native-candidate` writes an incomplete native-only copy
under this project's ignored `private/` directory. It never replaces its input,
never overwrites existing output and never launches that output. Keep it for
static comparison; this is not an instruction to install or play it. The timer
policy and all real-client tests are unfinished; locating the clock does not
establish that the legacy freeze is necessary or correct for the port.

The builder requires the exact input SHA-256, original byte guards and surrounding
code guards. It checks RVA/file-offset mappings and refuses overlap, bad lengths,
unsupported inputs and an unexpected output checksum. Expected candidate hash:

`04a9ccffd76f65806c371c380c5e245125ca532a0725404d071ef317498667fa`

The offline candidate changes 37 bytes of instruction spans at three sites; fewer
individual byte values differ because some instruction bytes are retained. No
other ranges are intentionally modified. It has no map-specific patches, which
**does not establish all-maps support**.

## Validation completed here

18 offline tests passed, including one using the actual private executable and
17 tests of guards/output preservation/observation interpretation. Static
inspection confirmed the file's version, architecture, instruction boundaries,
replacement lengths and the third block's branch destinations. The input hash
remained unchanged after building the private candidate.

The original collector has also been executed successfully on Windows for one
main-menu capture and a later solo No Mercy countdown capture. The native-timer
reads are now observed on Windows, with live values matching the visible clock.
An attempted isolated i386 CPU fixture could not run here (ELF32 loader rejected
the file; an ELF64 compatibility-segment attempt faulted). Neither attempt is
counted as a passing test or included in the shareable kit.

These checks do not validate networking or game behavior. The
remaining gates are four real clients on each map, native No Mercy mode, combat,
extra-slot death/revive, results, another round and two-player regression.
Candidate map labels from Fluffy's tool: Rail Yard, Requiem for War, Urban Chaos,
Mining the Depths, High Seas Fortress, Catacombs, Steel Beast, Rooftop, Creature
Workshop and Liquid Fire. Confirm that inventory against the actual installation
and add any additional maps before claiming complete coverage.

## Local development

```text
python -m unittest discover -s tests -v
```

The private-executable test is skipped unless RE6_TEST_INPUT points to the supplied
fixture. A suite with that skip must not be reported as full private-executable
validation. No game executable belongs in a commit, archive or publication.

### Session diagnostics update (2026-11-07)

The current collector writes schema 3 and adds bounded lobby-slot observations
and a separate player-object presence table. Static tracing found a six-entry
host admission search and distinct no-free-slot and map-availability branches.
These additions make admission and object creation separately observable;
they do not increase the candidate's validation level.

The current suite passes **52 offline tests** on Linux x86-64 with the existing
C compiler and private executable fixture. Three native selector checks are
skipped on other platforms or without a compiler; the private-executable test
is skipped without its fixture. The new session and object-table reads have now
succeeded in both solo No Mercy and a host-lobby capture. The lobby records
capacity 2, one available partner entry and no spawned player objects. See the
[session admission analysis](docs/SESSION-ADMISSION.md) for native evidence,
field meanings and limits. No additional game patch or timer write was added.

The unchanged solo/lobby baseline is complete; another identical capture is
unnecessary. For reference, the read-only command for a normal Mercenaries
two-player Create Game lobby, with the existing trainer deactivated, is:

```powershell
py -3 .\probe_windows.py --pid (Get-Process BH6).Id --context mercenaries-lobby --samples 20 --delay 10
```

Return to the lobby during the delay and stay there without starting a round.
The `--context` argument is only a label; it does not select a game mode or screen.
This records slot configuration and player
object presence candidates; the generated `private/probe-*.json` stays private.
It does not apply the offline candidate or request a four-player playtest.

### Native selector check (2026-11-07)

A Linux x86-64 fixture now executes the exact 27-byte candidate selector using
shared instruction encodings and a synthetic RNG. All 624 occupancy/input
cases and separate retry/exhaustion checks pass. This is narrower than a full
32-bit ABI or Windows test and does not validate gameplay. The real retry loop
remains unbounded; no executable patch bytes changed. See the
[method, results and limitations](docs/NATIVE-SELECTOR-CHECK.md).

## Remaining development access

This cloud workspace has the privately supplied executable and returned diagnostic
reports, not a complete playable RE6 installation, Windows game execution access,
or four authenticated test clients. It cannot execute the real-client bot suite.
The three-site native-only candidate is reproducible here, but the appropriate
timer policy, larger-session admission/spawning and extra-slot death/results
behavior still need controlled game execution. Do not install the candidate in
an original Steam installation or count solo timer observation as a map PASS.

## Research records

- [Trainer compatibility and sources](docs/RESEARCH.md)
- [Native patch investigation and map test matrix](docs/PATCH-INVESTIGATION.md)
- [Research notes](docs/NOTES.md)
- [Session admission and player-object observations](docs/SESSION-ADMISSION.md)
- [Native selector execution check](docs/NATIVE-SELECTOR-CHECK.md)
- [Experimental lobby trial and undo](docs/LOBBY-TRIAL.md)
- [Three-client joining check](docs/THREE-CLIENT-ADMISSION.md)

This repository contains the RE6 work originally developed in the cloud setup
workspace. Game executables, assets, raw captures and private machine notes are
excluded. Publishing this source does not make the candidate gameplay-ready.
