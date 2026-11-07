# Resident Evil 6: Mercenaries with four or more players

Research started 2026-11-07. No game or mod binaries available; no gameplay tests run.

## Observations

- The owner requests Mercenaries and Mercenaries No Mercy with at least four players. Their attempted lobbies stop at two. This is a user report, not a reproduced test.
- No RE6 entry or game write-up was found in the checked-out hub by `rg` on 2026-11-07. Source: [directory](https://github.com/cranebeaker/coop-anything/blob/main/data/directory.yaml).
- Read AGENTS.md, triage, research and revival guidance; synchronized the hub checkout with `git pull --ff-only`.

## Target identity (unknown)

Store, game build, executable SHA-256, OS, exact Fluffy tool/version: unknown. Requested from owner; do not apply binary patches until these are established. Engine: unknown pending cited evidence or local inspection.

## Derived

- A lobby-size setting alone would not demonstrate four players spawning, playing and sharing enemies, score, timer and results.

## Hypotheses

- None confirmed. Investigate mod-manager versus trainer features and mode-specific player caps separately.

## Unknowns

- Whether a usable four-player Mercenaries / No Mercy mod exists, its compatibility and license.
- Whether the cap occurs in lobby creation, join admission, game launch, spawning or replication.

## Checks run

- Hub checkout synchronized; no game testing.

## Research log

- Anonymous GitHub searches for RE6 / Resident Evil in the hub's issues and PRs found unrelated Revelations claims [#298](https://github.com/cranebeaker/coop-anything/issues/298) and [#299](https://github.com/cranebeaker/coop-anything/issues/299), read in full. No RE6-specific work found in these searches; not a proof that none exists. Numeric `6` also matched unrelated PR #6, excluded.
- Anonymous repository searches for `"resident evil 6"`, `RE6 trainer`, `"resident evil 6" multiplayer`, `resident evil 6 mercenaries` and `FluffyQuack` did not locate a four-player Mercenaries implementation. Sources: https://github.com/search?q=%22resident+evil+6%22&type=repositories and https://github.com/search?q=RE6+trainer&type=repositories . Promotional cheat repositories are not evidence of a multiplayer implementation.
- Environment policy denied direct reads of Fluffy's site, Google search and the Steam store (HTTP CONNECT 403). Proposed research-domain additions in the environment draft; no publication performed.

## Additional observations

- All three pages (23 results at read time) of the exact-title GitHub repository search were inspected. This is a bounded search, not an exhaustive survey.
- [FluffyQuack's GitHub repository search](https://github.com/search?q=user%3AFluffyQuack&type=repositories) was inspected across both pages; no RE6 trainer source was identified there.
- [GPT-6 RE6 Trainer](https://github.com/GPT-6-RE6-Trainer/GPT-6-RE6-Trainer) README was read, not its releases. It describes enemy/scene/player controls, not a demonstrated four-player multiplayer implementation. It is a different author/project.
- [RE6CrashFix](https://github.com/x0reaxeax/RE6CrashFix) README was read on its `master` branch: a display-mode enumeration startup fix, identifying the Steam executable as `BH6.exe`. No relationship to lobby expansion was established. No software was downloaded or run.
- Broad GitHub issue searches containing standalone numeric tokens returned unrelated numbered issues. Excluded those results; do not treat them as evidence about RE6.
- Authenticated `gh` operations were not used. Public issue/PR pages were read anonymously instead. A claim issue, fork or PR requires permission before using the owner's account, per AGENTS.md.
- No directory entry added yet: remaining blocked source checks must establish the project's identity or justify a carefully scoped gap entry. Do not describe RE6 generally as a game with no co-op.

## Hypotheses to test (not patch instructions)

- A larger-lobby native game mode might provide useful session/actor infrastructure, but compatibility with Mercenaries and No Mercy is unknown. No mode-swap recipe has been verified.
- The cap may exist at multiple layers: session advertisement, join admission, readiness/start logic, spawning or replication. Neither a larger lobby limit nor four visible actors proves a complete four-client match.

## Handoff

See [README.md](RESEARCH.md) for the research boundaries, identity prerequisites, pending sources and real-client QA matrix. No executable patch was produced. Continue source research after the proposed network access is applied, then inspect an explicitly identified test build before implementing anything game-specific.

## Follow-up session: 2026-11-07, after network settings publication

### Observed

- Re-read AGENTS.md and private local state, synchronized with `git pull --ff-only origin main`, and checked runtime policy. The newly allowed Fluffy/Steam hosts are enforced and direct HTTPS reads now succeed. No environment settings were re-saved or published in this session.
- [Fluffy's homepage](https://www.fluffyquack.com/) confirms the manager includes trainers, identifies RE6 among MT Framework titles supported by ARCtool, and links its official archive/source directories.
- Retrieved the official 3,319,205-byte [manager ZIP](https://fluffyquack.com/tools/modmanager.zip) for text/static inspection only. SHA-256 `4ab66d608403e0e73b22af571c65db53bed3e18162fbfd161c50d7d7e1daf139`; manager identifies as v3.084, changelog date 2026-09-22. No included software installed or executed. These measured hashes are not independently published author checksums.
- README explicitly lists RE6 v1.0.6 support and the exact `6 players in mercs duo create menu` function. Changelog v1-53 (2014-02-15) separately documents enabling `host 6 player no mercy` before lobby creation and its automatic timer freeze. README says only the host needs the trainer for Mercenaries hosting, and describes port 9950 as optional trainer-poke synchronization.
- Static ASCII strings in the current manager include `8 players in mercs duo create menu`, `7 private slots in mercs duo create menu`, `Host 6-player Mercenaries: %s` and `Show advanced trainer functions: %s`; default config has `trainer_advanced: 0`. This conflicts with the README's exact menu wording. Runtime UI behavior and eight-player support are unknown. Do not silently translate the old README into a current-version guarantee.
- Read the author's [Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=253237426), which advertises hosting six-player Mercenaries, and [2021](https://steamcommunity.com/app/221040/discussions/0/4652759797628721960/) / [2024](https://steamcommunity.com/app/221040/discussions/0/4406291470270588709/) reports that require v1.0.6 and report v1.1.0 failure. These are not locally reproduced compatibility findings.
- Read [a 2023 player hosting report](https://steamcommunity.com/app/221040/discussions/0/3874841497818313842/), [the Russian historical workaround guide](https://steamcommunity.com/sharedfiles/filedetails/?id=705194122), and [the 2015 No Mercy guide/comments](https://steamcommunity.com/sharedfiles/filedetails/?id=415304918). Record their failure reports as QA cases; do not claim the workaround works on a current build.
- The Russian guide calls the breaking update `1.1.6`; other threads say `1.1.0`. Version notation is unresolved; do not use the Russian update as exact binary identity.
- [2024 detailed guide](https://steamcommunity.com/sharedfiles/filedetails/?id=3365876715) was read for text/comments. Its actual instructions are images on `images.steamusercontent.com`; direct access returns CONNECT 403, so image contents were not read.
- Raz0r alternative: [2024 six-player discussion](https://steamcommunity.com/app/221040/discussions/0/4406291470270588709/) explicitly admits insufficient testing. [Character guide](https://steamcommunity.com/sharedfiles/filedetails/?id=3151776849) and [slot/bot guide](https://steamcommunity.com/sharedfiles/filedetails/?id=1865523188) document other trainer capabilities but do not prove four-human v1.1.0 Mercenaries or No Mercy. No alternative trainer downloaded.
- Forum/Google ordinary reads now connect but return JavaScript shells. Existing Chromium/Playwright were tried; Chromium rejects the session proxy CA. An isolated local NSS trust database populated with the already installed public session CAs did not fix that browser error. TLS verification was never disabled. The readable author ZIP/Steam sources above remain sufficient for the documented compatibility finding.

### Derived

- The existing Fluffy trainer is the first implementation to investigate, rather than writing multiplayer from zero.
- v1.0.6 is the documented compatibility target. On v1.1.0, the same symptoms are consistent with a trainer/build mismatch; activation-order advice alone is not a demonstrated fix.
- A mod-manager version update, an eight-slot label, an online-slot toggle or AI bots do not prove that four human clients can finish both modes.

### Unknown / blocked

- Exact v1.1.0 executable hash and OS of an authorized test installation; no game files are available here.
- Whether any current patch/trainer successfully supports four humans in both modes on v1.1.0.
- An official reproducible acquisition route for a historical game build; do not replace it with third-party executable uploads.
- Root cause in actual game memory and all real-client QA outcomes.

### Local changes

Updated README with cited historical setup, current-package wording discrepancy, version limitations and QA requirements; added the existing Fluffy project to the directory with `community-reports` QA and `partial` status. No account use, contacts, claim issue, fork, PR or publication.


## Correction: historical labels are not current UI instructions (2026-11-07)

### Observations

- The official v3.084 package statically contains `Host 6-player Mercenaries: %s`, already recorded above. This is consistent with the observed On/Off UI control. Details of owner-supplied evidence remain in ignored `local/`.
- Previous user-facing advice incorrectly presented the historical README's `6 players in mercs duo create menu` and 2014 changelog's `host 6 player no mercy` as current menu instructions. That advice is withdrawn; these are historical documentary claims, not two additional controls users should be expected to find.
- Updated the README and directory notes to make the distinction explicit. No software was run and no game test occurred.

### Unknowns

- Whether the current single toggle handles both requested modes, when it must be enabled, or how it behaves against the exact v1.1.0 executable.
- The community-reported v1.1.0 incompatibility remains a plausible explanation, not a reproduced diagnosis. Do not infer that an activated trainer proves every individual feature supports the attached game.
- An Off value in a screenshot does not prove the owner never tested On, and switching it is not a verified solution.

## v1.1.0 patch exploration (2026-11-07)

### Observations

- User requested exploration of a v1.1.0 patch, at least four players, No Mercy and all maps. Target availability and owner-specific evidence remain in `local/`.
- Re-synchronized the hub checkout. Existing source/access restrictions remain unchanged; no draft or publication operation performed.
- Traced the pinned official manager's Host 6-player control past its string, through its menu object, to a byte flag and three native-code patch records. The update path also makes a recurring poke call with ID 0x28 and value 0xa6; its game semantics remain unknown.
- Independently reconstructed and disassembled the three native-code replacement buffers. Verified their lengths and legacy offset operands; the third contains a backward branch outside its replacement span. Checked the PE imports used by the reader/writer helper.
- Extracted all ten S1210-S1219 No Mercy stage labels from the same pinned manager. These are not verified v1.1.0 stage inventory or gameplay results.
- Detailed evidence, addresses explicitly distinguished between manager VAs and unverified game offsets, acceptance matrix and next steps are in [PATCH-INVESTIGATION.md](PATCH-INVESTIGATION.md).

### Derived / hypotheses

- Updating the lobby display or one maximum-player number alone would not reproduce the inspected trainer's behavior; all three code records and the recurring write need to be understood.
- A narrow adaptation of existing native hosting logic is the first candidate. Valid v1.1.0 patch locations, original instructions, game-mode meaning and per-map behavior cannot be derived from the trainer's old target constants alone.

### Blocker

- No BH6.exe, installed game assets, current process or remote Windows connection is available here. Static porting needs the exact private v1.1.0 executable; real-client QA needs isolated test installations. No generated file is a working game patch.


## Uploaded v1.1.0.0 executable: static port candidate (2026-11-07)

### Observed

- Privately received and identified the uploaded executable. File/product version resource is 1.1.0.0; PE32/x86, image base 0x400000 and image size 21671936. Input archive/executable identity and owner-specific paths are kept in ignored local storage. No binary is published or in the shareable kit.
- Strong native matches for all three trainer code sites are at RVAs 0x612cdd, 0x610b21 and 0x610b3a in the supplied build. The expected two-player instructions and surrounding control flow were checked; all three have a +0x37c0 shift, but that difference was not used as the sole locator.
- Resolved the recurring trainer write to its RE6-specific dispatch: a timer-freeze operation using 120.0f, not a game-mode change. Current pointer roots are supported by native references plus the [autosplitter](https://github.com/TheDementedSalad/RE6-Autosplitter/blob/main/Resident%20Evil%206%20Autosplitter.asl). The timer field itself remains a read-only live candidate, not a validated write address.
- Built an offline native-only candidate in a separate local game project, preserving the original upload. The builder requires the exact input hash and checks original bytes, surrounding instructions, RVA/file mapping and output checksum; it refuses in-place output, overwrite and path escape.
- Added a read-only Windows collector for native-code comparison, old-offset corruption detection and candidate mode/stage/timer observations. No game input, launch, memory write, injection or account operation is performed by it. Windows API execution remains untested here.
- Ran 16 offline tests successfully, including the actual private image. No game client was run; no map, player synchronization, death or results claim follows from those tests. See [PATCH-INVESTIGATION.md](PATCH-INVESTIGATION.md) for the complete static evidence and remaining all-map gates.

### Next runtime prerequisite

The native-only candidate is not ready to install. Collect read-only observations from the Windows process to validate the live pointers and ensure no old trainer writes are active before planning a reversible runtime implementation and real-client bot suite.


## First read-only live baseline and timer-path refinement (2026-11-07)

### Observed

- A returned Windows main-menu capture matches the pinned image identity. All
  three relocated code spans are original; all historical target locations
  match disk during the six samples. The collector's original read-only Windows
  path is now observed to execute. Mode and timer candidates are zero at the
  main menu; no active No Mercy inference follows. Raw report and owner context
  remain ignored in local/.
- Further native tracing identifies float subtraction/addition and initialization
  at mode-object +0x486c, with adjacent state/elapsed fields. See the exact VAs
  and evidence in [PATCH-INVESTIGATION.md](PATCH-INVESTIGATION.md). Separate
  constructors register mode and game-info roots; their heap adjacency is not
  an assumed invariant.
- Extended the read-only collector to compare both timer derivations, preserve
  a user-reported screen context and delay sampling while game focus returns.
  Eighteen offline tests passed with the actual private image; the new fields
  have not yet been captured on Windows.
- Native CPU fixture attempts were unsuccessful (ELF32 rejected, compatibility
  segment fault). They are private failed experiments, not a validation result
  or part of the distributable source kit.

### Remaining prerequisite

Correlate the native timer candidate with a normal solo No Mercy countdown using
read-only observations. This is diagnostic data collection, not owner-driven
four-client QA. Multiplayer, deaths/results and every all-map gate remain NOT RUN.
No original installation was modified, software installed, account used or work
published.


## Live No Mercy countdown corroborated (2026-11-07)

### Observed

- A second schema-2 capture records twenty samples in solo No Mercy, mode80
  (0x50), stage1212. Visible clock (~0:52 to0:33) and Urban Chaos were separately
  confirmed. Raw report and context remain private in ignored local/.
- Native timer decreased18.99976 seconds over19.01187 wall-clock seconds; the
  adjacent elapsed value rose19.00409 seconds. Both timer address derivations
  agreed throughout; current code spans stayed original and historical sites
  matched disk throughout.
- Traced the slot initializer's constructor/factory/type registration to
  uIdStartUp34, instantiated by startup paths with explicit mode0x50 branches.
  Exact addresses are in [PATCH-INVESTIGATION.md](PATCH-INVESTIGATION.md).

### Derived and unknown

- Direct mode-root +0x486c is now corroborated as the live countdown in this
  context. No repeated timer-only capture is needed. This does not decide the
  write/freeze policy or validate any multiplayer capacity.
- Three-site native port remains an unplayed candidate. All-map/four-client
  gates stay NOT RUN, including Urban Chaos; a solo diagnostic is not a map PASS.
- Full game assets, controlled Windows execution and real-client bots are still
  unavailable here. No game install/save changed, account used or work published.


## 2026-11-07: continued in gigart

- The source kit and existing research were transferred to this repository and
  pushed at 98347c0. Earlier statements that nothing was published describe those
  earlier investigation steps. Private binaries and captures remain excluded.
- Traced host admission at 0x5197b0 to the six-entry free-slot helper at 0x5515a0,
  response bytes for no-free-slot and map-mask rejection, and the success-path
  slot-state assignment. See SESSION-ADMISSION.md for addresses and limitations.
- Located sPlayer metadata and its instance global; getter 0x590b00 reads eight
  player-object entries at manager +0x24. Non-null pointers are presence candidates,
  not alive/controllable/client proof. No extra executable patch was introduced.
- Added schema-3 read-only session and player-object observations, explicit
  unknown handling, duplicate-object detection and root-change discard behavior.
- All 32 offline tests passed with the private executable fixture: 18 existing
  checks and 14 new observation/interpretation checks. CLI help and diff checks
  passed. New Windows reads, multiplayer and all-map QA have not run.
- Next observation target is the normal Mercenaries two-player Create Game lobby,
  not another timer-identification capture. Real-client admission/spawning,
  timer-write policy, extra-slot deaths/results and all maps remain unverified.

## 2026-11-07: live schema-3 solo baseline

- Received twenty Windows samples for the exact pinned executable. The command
  label says mercenaries-lobby, but the user explicitly confirms solo No Mercy
  was running. Recorded the confirmed context instead of treating the label as
  automatic state detection. Raw capture and analysis remain ignored in local/.
- Mode80/stage1212 throughout. All new session and player-object read groups
  have stable roots and complete fields. Slot0 state2/kind3; other seven empty.
  One distinct player object at index0, no duplicates. The new collector's
  reads now have Windows observation evidence in a solo context.
- Session-type candidate4, create-capacity candidate0, stage-index candidate0,
  randomized slots0. These values are not evidence of an online-lobby failure;
  the host admission path checks for session-type1. See SESSION-ADMISSION.md.
- Original instructions remained at all three candidate spans; all historical
  sites matched disk. Timer advanced with a roughly sixty-second positive
  adjustment, consistent with a time bonus; no bonus event was independently
  observed and no timer freeze is inferred.
- No new executable patch, game write or gameplay test. The existing offline
  suite remains the previous 32-test result; only documentation and observation
  metadata changed for this capture. No repeated solo/timer baseline needed.
- Next missing capture remains the standard Mercenaries two-player Create Game
  lobby, staying there without starting a round. Clarified that --context only
  labels the report; it does not switch the game mode or screen.
