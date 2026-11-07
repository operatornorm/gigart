# Experimental lobby-capacity trial

This is the next development experiment, **not a finished four-player No Mercy
mod**. The native candidate is unchanged. `native_trial.py` can now apply or
restore its three code spans in one already-running Windows test process.
The first returned Windows apply/inspect reports now show successful application
and six-slot initialization. Live restore and rollback have not been observed.
The trial can fail, freeze or crash the test process; it belongs on an isolated
test copy. No game executable is included in the kit.

The first question is narrowly scoped: **does entering a fresh lobby after the
native changes initialize six distinct slots and five available partner entries?**
The first returned trial answers this configuration question positively. It
still leaves network admission, No Mercy spawning, timer policy,
deaths/results, subsequent rounds and all maps unverified.

## Prepare the test copy

1. Keep the original game installation and saves untouched. Make a separate copy
   of the complete game folder, outside the original install, for this experiment.
   Copying just BH6.exe is not a complete runnable test installation. A separate
   game folder does not by itself provide separate Steam saves or a test account.
2. Extract the updated source kit into its own folder. Python 3.10+ is sufficient;
   the trial tool needs no pip packages or installed compiler on Windows.
3. Deactivate Fluffy's trainer, restart the game from the test copy and stay at
   the **main menu**, before creating a lobby. The manager can remain open.
4. Know the exact path of that copy's BH6.exe. The write command requires it and
   refuses a process whose executable path differs. If Steam launches the original
   installed executable instead, the tool must refuse; do not substitute the
   original path to get past that check.

The test-copy path is supplied by you; the tool cannot independently discover
which folder is your original installation. It never launches the game, operates
Steam or writes a game file, save, mode field or timer. Applying the candidate
changes process memory and briefly suspends the test process.

### If the test copy says “Failed to initialize Steam”

Having Steam open is necessary but does not guarantee a direct launch receives
the app-ID context that Steam normally supplies. The supplied executable calls
`SteamAPI_Init` at preferred VA 0xf3811d and displays this fatal error when it
returns false. The subsequent ownership check uses app ID **221040**. That
identifies the failure path, not its root cause on a particular PC.

For a local test-copy launch, the standard Steamworks app-ID hint is a file named
`steam_appid.txt` beside the copied executable, containing only `221040`. This
does not remove the game's later ownership check. Keep Steam running under the
same Windows user. In PowerShell, for the example test-copy location:

```powershell
Set-Content -LiteralPath "D:\RE6-Test\steam_appid.txt" -Value "221040" -Encoding ASCII
Start-Process -FilePath "D:\RE6-Test\BH6.exe" -WorkingDirectory "D:\RE6-Test"
```

Create this hint only in the separate test copy. Once the main menu appears,
check the actual executable path before any candidate write:

```powershell
(Get-Process BH6).Path
```

It must identify `D:\RE6-Test\BH6.exe` (or your actual test-copy path). A missing
app ID is only one possible reason for Steam initialization to fail; this
launch method has not been verified on the owner's PC. If the same error remains
or the running path is the original installation, stop before applying the
candidate. The new hint can be removed from the copy to undo this launch setting.
Do not substitute the original executable path to defeat the trial's intended
test-copy isolation.

## Apply at the main menu

From the new kit folder, replace `D:\RE6-Test\BH6.exe` with your actual test-copy
path. Exactly one BH6 process should be running:

```powershell
py -3 .\native_trial.py --pid (Get-Process BH6).Id --test-exe "D:\RE6-Test\BH6.exe" --apply
```

This is an explicit write command. Without `--apply` or `--restore`, the tool is
read-only. It checks the exact original executable hash, output candidate hash,
module base/size, all three live instruction/context guards and the historical
trainer targets. It requires the observed menu scene, no active host/join session,
no other occupied slots and an empty player-object table (or a readable null
player-manager root). Unsupported or unreadable states are refused.

The state and code checks are repeated while process suspension is held. Code
writes are read back, the instruction cache is flushed and memory protections
are restored. A partial write or failed verification triggers rollback of every
attempted span, including the partly written one. A failed rollback or protection
restore is reported explicitly; close the test game in that case. A failed
process resume may require ending the test process with Task Manager. An abrupt
termination of Python/Windows cannot guarantee rollback or resume.

The main-menu checks deliberately refuse an existing lobby. The initialization
code must run **after** applying the candidate; applying it to an already-created
two-slot lobby would not reinitialize that lobby's data.

## Inspect a newly created lobby

After a successful apply, create a fresh **standard Mercenaries duo lobby**.
Use an invite-only/private session and remain alone in it. Advance past the
Worldwide/Country settings to the player/character-selection waiting screen.
**Do not start a round or invite participants for this first experiment.**

Run the tool again with no write flag:

```powershell
py -3 .\native_trial.py --pid (Get-Process BH6).Id
```

The UI may still draw only two slots; the report checks actual observed fields.
The expected result requires all three candidate spans, capacity 6, five empty
partner entries, a six-element permutation of randomized slot indices, untouched
historical trainer targets and no spawned player objects. It prints:

```text
SIX-SLOT CONFIGURATION OBSERVED; NETWORK/NO MERCY/GAMEPLAY NOT VALIDATED
```

That message is a configuration observation, not proof that anyone can join or
play. If the expected configuration is absent, do not launch a round or guess
additional offsets. Attach the generated `private/trial-apply-*.json` and
`private/trial-inspect-*.json` for analysis. If an operation refuses to run,
provide its exact console error; do not weaken its guards.

## Undo

Closing the game discards these process-memory changes; the on-disk executable
was never patched. To restore while keeping the process open, leave the lobby
and return to the main menu, then run:

```powershell
py -3 .\native_trial.py --pid (Get-Process BH6).Id --test-exe "D:\RE6-Test\BH6.exe" --restore
```

Restore requires all three known candidate spans and their matching surrounding
code; mixed/unknown states are refused. It restores only these three spans,
not unrelated trainer changes. Restart with Fluffy's trainer deactivated if the
old trainer locations differ from disk. Closing the process remains the way to
discard an unknown in-memory state without editing the installation.

### First returned Windows result (2026-11-07)

The apply report shows the original instructions at all three sites before
application and the exact candidate bytes afterward. The preflight snapshot is
the observed menu scene, mode 0, session type 0, empty slot configuration and no
player objects. Neither snapshot shows any mode/timer change. Historical trainer
locations match disk before and after.

The subsequent fresh standard Mercenaries duo-lobby inspection records:

| Field | Result |
|---|---|
| Mode / session type | 30 / 1 |
| Capacity candidate | 6 |
| Host slot 0 | Kind 3, state 1 |
| Partner entries 1–5 | Kind 1, state 0: five available entries |
| Entries 6–7 | Disabled |
| Randomized prefix | 2, 1, 3, 4, 5, 0: six distinct values |
| Player objects | None, as expected while waiting alone in the lobby |
| Native code | Exact candidate spans still present; historical targets match disk |

The assessment was independently recomputed from the returned fields rather
than trusting the report's assessment string. This is a **six-slot initialization
observation**, not a successful six-client Steam lobby or a playable multiplayer
result. Only one apply and one lobby snapshot have been returned. No repeat of
this same unchanged configuration capture is needed.

The immediate next check is live restoration: leave the lobby, return to the
main menu and run the restore command above, then return its private report.
If the process has already been closed, its in-memory changes were discarded;
do not reapply merely to produce an undo report. Restore/rollback behavior is
still backed by synthetic tests until an actual restore report is returned.

## Validation performed here

All **52 offline tests** pass on the current Linux x86-64 host with its existing
compiler and the private executable fixture. Seventeen new trial tests cover
apply/restore equality, complete preflight, historical-site guards, changed code,
partial writes, bad readback, interruption, rollback failure, menu restrictions,
candidate-lobby interpretation and mocked suspension/protection/cache behavior.
Those Windows API mocks are not evidence of a Windows run. Separately, the
returned apply report and subsequent lobby observation now provide live evidence
for one successful Windows application path. The cloud itself has not opened a
Windows game process. Live restore/rollback, peer joining and gameplay remain
unverified; no multiplayer round was run as part of this trial.
