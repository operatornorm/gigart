# Resident Evil 6: Mercenaries with four or more players

Research started 2026-11-07. Current result: three-player admission captured;
three-player standard Mercenaries and No Mercy gameplay reported by the user.
See [the current evidence](THREE-PLAYER-RESULT.md). Earlier dated entries preserve
their status at the time. Raw game inputs and reports are private.

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

## 2026-11-07: duo-lobby baseline and native selector check

- The subsequent twenty-sample schema-3 report is consistent with the requested
  waiting host lobby: session-type1, capacity2, slot0 kind3/state1, slot1
  kind1/state0, remaining slots disabled. Randomization prefix1,0. Player-object
  table fully readable and empty. All session/object fields stable across
  19.016589 seconds; raw capture and private analysis remain ignored.
- The native helper would find partner index1 for a kind1 request. This is not
  an actual join or a measured network-service member limit. All current code
  spans original and historical sites matched disk throughout.
- Mode80 persists while actual-stage1102 and timer/elapsed values are constant.
  That combination shows why a mode value alone cannot classify a running
  match or selected lobby mode. No repeated unchanged lobby/solo capture needed.
- Added a fixture that executes the exact candidate selector bytes using
  instructions shared between x86 and x86-64, a low-address object and a bounded
  synthetic RNG. All 624 occupancy/input cases pass, plus repeated-occupied-draw
  and full-mask exhaustion checks. Full 32-bit ABI, real RNG and Windows remain
  untested. Earlier failed ELF32/compatibility attempts are not counted as passes.
- The fixture initially failed to assemble because of a stray character; fixed
  that source error and reran successfully. No game executable was launched.
- The full suite now passes 35 offline tests on the current host with the private
  fixture and existing compiler. No candidate replacement bytes changed, no
  memory/game-install writes occurred and no gameplay QA status increased.

## 2026-11-07: prepared reversible memory-only lobby trial

- Added native_trial.py. Default mode uses the existing read-only reader;
  apply/restore require explicit flags and an exact matching test-executable
  path. No actual game file, process memory, timer, mode or save was changed here.
- Write preflight pins original and candidate hashes, preferred module base/size,
  live instruction/context guards and unchanged legacy targets. Requires the
  observed menu scene, inactive session and absent player objects/other peers.
  An existing lobby is refused because initialization must run after patching.
- The Windows backend uses NtSuspendProcess/NtResumeProcess around state checks,
  the transaction and rollback. Writes restore protection and flush instruction
  cache. This backend has only mocked tests here; no Windows process was opened.
- Seventeen new tests pass for preflight, transactional restore, partial writes,
  readback failures, interruption, rollback failure, state restrictions,
  six-slot interpretation and mocked backend controls. Full suite:52 offline
  tests passed with private fixture and existing compiler. CLI help checked.
- Packaged instructions require an isolated complete test copy, followed by an
  empty private standard-Mercenaries lobby check. No round/extra participant is
  requested; this is a configuration experiment, not human acceptance QA.
- Original candidate bytes and unresolved timer policy remain unchanged. A
  successful configuration check would still leave actual peer admission,
  No Mercy spawning, extra-slot deaths/results and every-map QA unverified.

## 2026-11-07: test-copy Steam initialization blocker

- Owner reports “failed to initialise steam” / “fatal error” on direct launch
  of the copied game, despite Steam being open. No candidate application was
  reported; do not classify this as a patch failure.
- Checked the supplied image's Steam imports and native startup path. Call at
  VA0xf3811d is SteamAPI_Init; a false return displays the matching message at
  VA0x16e53d4 and exits. Subsequent app ownership check at VA0xf38170 supplies
  0x35f70 (221040). The exact cause of the failed initialization remains unknown.
- Documented the standard local Steamworks app-ID hint in the copied directory,
  followed by a running-image-path check. It has not been verified on this PC.
  No original installation, executable, Steam account or DLL was modified here;
  the existing trial guards and candidate bytes remain unchanged.

## 2026-11-07: first Windows native application and six-slot lobby

- Owner reports the copied game launches after adding the app-ID hint. The
  Windows trial then reports successful apply from its accepted main-menu state.
  Returned apply snapshot: mode0/scene1102, session type0, empty slots/objects;
  all three spans original before and exact candidate afterward. Historical
  trainer targets match disk and observed timer/mode fields remain unchanged.
- Fresh standard Mercenaries duo-lobby snapshot: mode30, session type1,
  capacity6, host kind3/state1, partner slots1–5 kind1/state0, slots6–7 disabled.
  Randomization prefix2,1,3,4,5,0 is a permutation of0–5; player table empty.
- Independently compared the reported byte strings with candidate.json and
  recomputed the lobby assessment. It meets the six-slot configuration target.
  Raw reports, heap addresses and integrity hashes remain in ignored local/.
- This is one real Windows application and one initialization observation,
  not measured Steam member capacity, an extra-peer join or gameplay PASS.
  Live restore/rollback, No Mercy spawning and all-map behavior remain unknown.
- Next check: leave the lobby, return to main menu and restore original code;
  inspect the returned restore report. If process already closed, do not
  reapply just to undo. No further identical six-slot capture is required.
- Only observation metadata/documentation changed for these reports. The
  existing 52-test offline result remains the latest suite run; no new tests
  or candidate replacement bytes were introduced in this evidence update.

## 2026-11-07: live restore confirmed; three-player target accepted

- Returned restore report shows all three exact candidate spans before and
  original spans afterward. Historical trainer targets match disk throughout.
  Main-menu state, empty slot configuration and no-player-object observations
  are unchanged. Raw report and analysis remain ignored in local/.
- This establishes one successful live restore. Failure rollback is still
  covered by synthetic tests only, not an observed Windows failure case.
- Owner explicitly accepts three-player No Mercy as success; four-player
  support and complete map coverage remain separate goals. No candidate byte
  changes are needed for this target adjustment.
- Prepared a two-client then three-client joining protocol, keeping the first
  stage in a standard Mercenaries lobby without launching a round. Host-only
  patch initially; ordinary read-only collector after each peer joins. The
  empty-lobby-only native_trial assessment must not be used to judge an occupied
  lobby. No new unchanged baseline capture is needed.
- Static Steam matchmaking call at 0x419296 matches ISteamMatchmaking009's
  CreateLobby layout: the constant2 is lobby type, with the member count loaded
  from +0xad10. The shipped DLL/interface and live call arguments remain
  unobserved. Recorded source and limits in THREE-CLIENT-ADMISSION.md; no
  speculative additional patch was made.

## 2026-11-07: invitation availability gate

- Owner reports the usual two-player lobby flow disables the option to invite
  another participant once the partner joins. This was not a report of a failed
  peer test with the candidate; no extra peer has yet been observed here.
- Corrected the joining protocol's assumption that the second invite could be
  sent after the first peer joined. Proposed normal Steam invitations to both
  participants while the host is alone, then sequential acceptance. This is a
  diagnostic ordering, not a proven bypass of full-lobby/joinability checks.
- Traced native SlotPublicMax/SlotPublicOpen metadata strings, the public-open
  metadata update and the separate lobby-type/joinability wrapper at 0x41faa0.
  Steam SDK interface layout identifies SetLobbyType/SetLobbyJoinable calls;
  the latter passes false for internal type3. Source and limitations recorded
  in THREE-CLIENT-ADMISSION.md. Live emitted values remain unknown.
- No candidate bytes, memory-writing tools or process state changed. A disabled
  invitation UI must be distinguished from a rejected pending invitation and
  a game-level slot rejection before choosing a further implementation change.


## 2026-11-08: three-player result preserved; normal Steam wrapper

- Two supplied host captures have six consistent samples each, progressing from
  occupied slots 0–1 to 0–2, capacity 6 and exact candidate bytes at all three
  sites. These are lobby captures, independently establishing third-player
  admission. Their raw contents remain ignored in local/runtime-input.
- The host reports actual three-person gameplay in both standard Mercenaries
  and No Mercy without identifiable timer, score, item or enemy-spawn issues.
  Map/round coverage was not specified. Four or more real players are unverified.
- Tagged the original distributed source commit ea19ade as v0.1.0-tested and
  pinned its original kit hash, four runtime file hashes and full patch records.
  The records and those modules remain unchanged. No timer freeze was added.
- Added a separate Steam-install/process detection and GUI wrapper, with Apply
  and Restore using the original pause/guard/rollback backend. Only registered
  app 221040 paths qualify, followed by the original exact executable hash guard.
  No Python or test copy is needed for the packaged Windows executable.
- All 64 tests pass locally including the supplied executable. Public Linux
  CI passes with the private-input skip; Windows CI passes with platform/private
  skips, builds the standalone executable and checks its GUI startup. Those
  checks do not exercise the new wrapper against an actual running Steam game.
- Release packaging includes only the launcher, instructions, frozen build
  manifest and source-commit metadata, with SHA-256 download checksums.


## 2026-11-08: normal launcher confirmed; selected scene record correction

- Owner confirms the normal-Steam launcher works on their PC. A friend passes
  game/code detection but gets the scene refusal at Play Game / Extra Content /
  Mercenaries screens. Their scene value and selected index are not captured yet.
- Native getter 0x455380 reads [info + 0x412a4 + [info + 0x20] * 0x3ce4]. The
  original collector omitted the index. Constructor 0x5682a8 initializes four
  such records; the setter and scene initialization use the same indexed layout.
- Version 0.2.1 reads the selected bounded record and rechecks root/index. It
  retains the original stage-1102/session/player/transaction guards and the exact
  tested patch bytes. Invalid or changing reads have no record-zero fallback.
- Added read-only JSON export through Save diagnostics. The four original runtime
  source files remain frozen; the corrected lookup is in the normal-Steam wrapper.
- All 74 local tests pass with private input, including stale-record regressions
  in both directions and verification of native getter/constructor bytes. The
  affected friend's first live confirmation of the correction remains pending.


## 2026-11-08: scene-904 diagnostic; screen-independent inactive-session checks

- The returned 0.2.1 report shows stable record index0 and scene904, sessiontype0,
  all eight slot states0 and a stable empty player table. Exact original/current
  and historical code checks pass. Raw report remains ignored in local/runtime-input.
- This does not support the earlier nonzero-index explanation for this PC. The
  scene1102 requirement was too restrictive; no new scene allowlist is added.
- Version0.2.2 removes screen/menu/scene requirements. It verifies inactive
  session0/4, all eight slot states0 (including slot0), and no player objects;
  unreadable session/player data is refused. Checks repeat under suspension.
- The original write backend, four runtime source files and all three instruction
  patches remain unchanged. Existing lobbies must be recreated for initialization
  changes to take effect. Applying/restoring inside a lobby or round is refused.
- All80 local tests pass with private input. The reported idle scene904 and an
  unreadable scene are accepted; active/unknown state and post-Refresh state
  changes are refused before writes. The affected PC's live result is pending.
