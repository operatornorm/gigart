# Resident Evil 6: four-player Mercenaries and No Mercy

| | |
|---|---|
| Target | Four or more human players in Mercenaries and Mercenaries No Mercy |
| Engine | MT Framework, per [FluffyQuack's ARCtool description](https://www.fluffyquack.com/) |
| Versions inspected here | Private supplied executable, file/product version 1.1.0.0; main-menu and solo No Mercy memory captures, no multiplayer test |
| Existing project | [Fluffy Mod Manager / bundled RE6 trainer](https://steamcommunity.com/sharedfiles/filedetails/?id=253237426) |
| QA level | community-reports for the historical mod; no local gameplay validation |
| Last updated | 2026-11-07 |

## Finding

**An existing trainer feature targets this request; it is not a new co-op implementation.**
Fluffy's own [Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=253237426)
advertises hosting six-player Mercenaries. The README in the
[official manager archive](https://fluffyquack.com/tools/modmanager.zip) explicitly
lists RE6 **v1.0.6** as the supported trainer version. Its changelog describes a
separate No Mercy hosting option.

**Do not assume this works on v1.1.0.** A [2021 player report](https://steamcommunity.com/app/221040/discussions/0/4652759797628721960/)
says all players need v1.0.6 for standard Mercenaries and No Mercy, and that a
v1.1.0 participant crashes. A [2024 discussion](https://steamcommunity.com/app/221040/discussions/0/4406291470270588709/)
also reports Fluffy's expansion works with v1.0.6, not v1.1.0. These are community
reports, not a compatibility test performed here. A native-only offline port candidate now exists for the exact supplied v1.1.0.0
file; no current-build gameplay fix has been verified. See the patch investigation.

## Current control versus historical documentation

The current package contains **`Host 6-player Mercenaries: %s`**, matching the
On/Off control in the observed UI. Do not instruct players to find two additional
buttons named after historical documentation. Whether this single toggle handles
both standard Mercenaries and No Mercy, its required activation point, and its
behavior on v1.1.0 have **not been verified here**. A successful trainer attachment
or an available toggle is not itself a compatibility test for this feature.

The following table records what the bundled documentation says, **not current UI
instructions**:

| Historical wording | Documentary claim |
|---|---|
| `6 players in mercs duo create menu` | README describes selecting it while at Create Game to host expanded Mercenaries |
| `host 6 player no mercy` | Changelog v1-53 (2014-02-15) describes enabling it before lobby creation and automatically freezing the timer |

The README says joining players do not need the trainer for Mercenaries hosting.
This does **not** establish mixed-version compatibility; the player report above
specifically requires matching v1.0.6 clients. The trainer's separate IP/port-9950
network feature synchronizes trainer pokes according to the README. It is not
documented as the prerequisite for unlocking extra lobby slots.

Before applying game-specific instructions, record the actual game build,
executable SHA-256, OS and manager version. Work on an isolated copy and leave the
owner's installation and saves untouched, per [AGENTS.md](https://github.com/cranebeaker/coop-anything/blob/main/AGENTS.md).
Keep private machine details in ignored `local/`.

## Documentation versus current-package labels

The retrieved archive identifies itself as manager **v3.084**; its changelog dates
that release **2026-09-22**. Static ASCII inspection of `Modmanager.exe` found:

- `8 players in mercs duo create menu`
- `7 private slots in mercs duo create menu`
- `Host 6-player Mercenaries: %s`
- `Show advanced trainer functions: %s`

The bundled default configuration contains `trainer_advanced: 0`. These are
**observed strings/configuration, not a run of the UI or a game test**. The README's
six-player wording therefore does not exactly match the current binary's labels.
Neither an eight-slot label nor an embedded version string establishes that eight
humans can finish a match, or that the current game build is supported. Preserve
this discrepancy when comparing the owner's manager with older tutorials.

Archive provenance, retrieved 2026-11-07 over verified HTTPS from the author's site:

- URL: <https://fluffyquack.com/tools/modmanager.zip>
- Bytes: `3319205`
- Archive SHA-256: `4ab66d608403e0e73b22af571c65db53bed3e18162fbfd161c50d7d7e1daf139`
- `Modmanager.exe` SHA-256: `d7cfcdddb5b6193fc1b4dde4ec7f0e83a21ca186c449877d373132dd327a82f4`

These are measured hashes for reproducibility, not comparisons with an independently
published author checksum. The archive was read for documentation and strings;
no included executable was run, installed, patched or redistributed.

## Other research and reported limitations

- A [2023 thread](https://steamcommunity.com/app/221040/discussions/0/3874841497818313842/)
  includes a player reporting that they host six-player Mercenaries; the opening
  post requests No Mercy matches. This supports `community-reports`, not automated QA.
- An older [Russian setup guide](https://steamcommunity.com/sharedfiles/filedetails/?id=705194122)
  describes a Survivors-lobby workaround: change the trainer's game mode to
  `Mercenaries No Mercy - Multiplayer` and use `All teams same`. It reports
  character-selection problems, crashes when changing map/returning to the main
  menu, extra-player death bugs, and missing score display. Its own update says
  a later game update broke the trainer; it calls that version `1.1.6`, whereas
  other reports say `1.1.0`. That version notation is unresolved. Treat this as
  historical evidence, not a workaround verified on the current build.
- A [2015 No Mercy guide](https://steamcommunity.com/sharedfiles/filedetails/?id=415304918)
  links video demonstrations. A 2024 commenter reports a failure after a player
  in slot 3-6 dies. This remains an unverified report requiring a regression test.
- The [2024 detailed matchmaking guide](https://steamcommunity.com/sharedfiles/filedetails/?id=3365876715)
  has image-only instructions. Its text and comments were read; its instruction
  images were not accessible under the current image-host policy. Do not claim
  to have read those steps.
- The [2024 discussion](https://steamcommunity.com/app/221040/discussions/0/4406291470270588709/)
  mentions **Raz0r's Ultimate Trainer** as another possibility, but the commenter
  explicitly says six-player support was not tested. A [separate trainer guide](https://steamcommunity.com/sharedfiles/filedetails/?id=3151776849)
  covers character/scene changes, and a [bot guide](https://steamcommunity.com/sharedfiles/filedetails/?id=1865523188)
  documents slot controls and online peers. Neither establishes four real human
  clients playing both requested modes on v1.1.0. No alternative binary was fetched.

No verified official method of retrieving a matching historical game build was
established. Third-party game-executable and downgrade uploads linked by comments
were not adopted or downloaded. Manager updates are not proof that its RE6 trainer
was ported to a later game build. The manager's public source index was checked;
no source for this trainer was identified there, and its redistribution license
was not established.

## QA and next work

No RE6 gameplay tests ran. Offline candidate/guard tests, the directory validator
and documentation checks do not validate multiplayer. Before calling a solution ready, use [automated real-client QA](https://github.com/cranebeaker/coop-anything/blob/main/playbook/automated-qa.md)
on isolated copies to demonstrate:

- Host plus three distinct clients join, ready, load and control four actors in
  **standard Mercenaries**, then repeat independently in **No Mercy**.
- Each participant can attack, receive damage and use items; compare enemies,
  timer, combo, score and results against the mode's intended rules.
- Exercise deaths and revives in slots 3/4, match end, return to lobby, another
  round, supported map/character changes, disconnects and two-player regression.
- Record No Mercy load, crashes and desynchronization across repeated rounds.

The supplied executable is now pinned by hash in the patch investigation.
A clock-correlated solo No Mercy capture now corroborates the timer location.
Next reproduce the hosting failure in isolated test clients and distinguish
session creation/join admission from launch/spawn/replication limits. Port only
identified checks; do not publish a guessed memory offset or equate a lobby count
with a working match. Implementation belongs in a separate game repository.

## v1.1.0 patch exploration

The [patch investigation](PATCH-INVESTIGATION.md) now traces the current hosting
control to three native code patch records and a recurring trainer write. It
records the legacy sites, static verification and a ten-map No Mercy test matrix.
The supplied v1.1.0.0 executable was identified and strong native-code matches
were found. A native-only offline candidate and read-only Windows collector were
prepared in a separate local game project. No working multiplayer release or
gameplay validation is claimed.

The first returned Windows capture validates reading the original code spans
at the main menu, with no historical-site modifications during that capture.
A further native countdown path was traced, and the collector now compares its
mode-object field with the older timer derivation. Eighteen offline tests pass. A subsequent twenty-sample solo No Mercy capture
on Urban Chaos corroborates the native timer against the visible clock, with
mode80/stage1212 and both timer paths agreeing. Real-client/all-map tests remain
pending; no four-player or timer-write claim follows from this diagnostic.
