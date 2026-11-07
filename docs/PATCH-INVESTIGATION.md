# v1.1.0 Mercenaries / No Mercy patch investigation

Status: **static port candidate and clock-correlated solo No Mercy capture; no multiplayer validation**.
Updated 2026-11-07. Three real players in No Mercy now count as a success target;
four-player support and complete map coverage remain separately tracked goals.
Standard Mercenaries remains a separate compatibility target
from the original request.

Follow-up: [session admission and player-object tracing](SESSION-ADMISSION.md)
now identifies the native six-slot admission search, separate map/no-slot
rejection paths and the eight-entry player-object table. Schema 3 observes those
fields read-only. Solo No Mercy and host-lobby captures now observe those fields
successfully; actual peer joining and all expanded multiplayer behavior remain
unverified. The [native selector check](NATIVE-SELECTOR-CHECK.md) passes in a
narrow Linux x86-64 fixture, not a full Windows/game execution environment.

The [first returned native lobby trial](LOBBY-TRIAL.md) now reports all three
candidate spans applied on Windows and a fresh standard Mercenaries lobby with
capacity 6, five available partner entries and six distinct randomized indices.
This is the first real initialization observation; peer admission, gameplay,
failure rollback and three-/four-player No Mercy remain unverified. A subsequent
restore report has now confirmed all three original spans were restored.

## What was actually traced

Source: [official Fluffy manager archive](https://fluffyquack.com/tools/modmanager.zip),
manager v3.084. The inspected `Modmanager.exe` SHA-256 is
`d7cfcdddb5b6193fc1b4dde4ec7f0e83a21ca186c449877d373132dd327a82f4`.
The archive hash and provenance are in [README.md](RESEARCH.md).
No included executable was run. This analysis does not establish that the owner's
manager is byte-identical.

The current **Host 6-player Mercenaries** control was traced past its label:

1. The string at manager VA `0x1402166e0` is referenced by string-table entry 655.
2. The menu object uses a `0x90`-byte stride; entry 655 starts at object offset
   `0x17070`. Initialization at manager VA `0x1400f1f41` binds its byte-valued
   control to manager VA `0x140313025`.
3. The update code at manager VA `0x1400e9175` reads that flag and applies/restores
   **three distinct native-code patch records**. Its calls resolve to a helper
   using `VirtualProtectEx` and `WriteProcessMemory`. The PE import table was
   checked to confirm those API identities.
4. The same path, when enabled, calls trainer routine `0x140116260` with poke
   identifier `0x28` and value `0xa6`. Follow-up tracing resolves this to a timer-freeze operation (message
   `Timer frozen.`, float value 120.0). Its live v1.1.0 timer location remains
   unverified. This must be investigated alongside the code patches.

All VAs beginning `0x140`/`0x141` above refer to the **inspected manager image**,
whose preferred image base is `0x140000000`. They are not addresses for BH6.exe.

## Three legacy code changes to locate in the actual game build

The initialization code at manager VAs `0x1401021e8` through `0x140102309`
constructs these records using the attached game module's base. The base is
obtained through the manager's module-enumeration helper; it is not a scanned
signature for each individual code site.

| Legacy module offset encoded in the trainer | Length | Static effect of replacement instructions |
|---|---:|---|
| `0x60f51d` | 3 bytes | Add six to EAX |
| `0x60d361` | 7 bytes | Store six into the dword at EDI + `0x4c` |
| `0x60d37a` | 27 bytes | Divide by the dword at EDI + `0x4c`, use the remainder as a bit index, test a mask, and branch |

**These are not verified v1.1.0 patch addresses. Do not write to them.** The
surrounding original game instructions and their semantics have not been read.
The third block includes a backward branch outside its replacement span, so
transplanting its bytes without checking the surrounding control flow is
particularly unjustified.

The trainer initializes original-byte buffers using `ReadProcessMemory`, then
uses the same patch-record lengths when applying/restoring replacements. Original
bytes captured from an arbitrary attached executable are not a substitute for
an expected-byte check against a supported build.

### Static checks completed

Using Python's standard library and the existing `objdump` installation:

- Verified the manager SHA-256 before interpreting addresses.
- Checked the label pointer, table index, object stride and RIP-relative binding
  to the toggle flag.
- Checked the three immediate operands that form the legacy target offsets.
- Reconstructed all replacement buffers independently from the initializer's
  immediate stores, including its zero-register stores; checked complete byte
  coverage and matched all three recorded lengths/content.
- Disassembled the replacement buffers as **32-bit x86**, independently of the
  64-bit manager that stores them.
- Resolved the relevant IAT entries to `ReadProcessMemory`, `WriteProcessMemory`
  and `VirtualProtectEx`.

This establishes what the inspected trainer prepares and writes, not what those
writes accomplish in any current RE6 build. No four-client, No Mercy, map-load,
combat or stability test was performed.

## Proposed implementation direction

Use the existing hosting logic as a map for a narrowly scoped v1.1.0 adaptation,
rather than replacing the game's multiplayer system. Keep a standalone patch in
its own game project, with original code only, unless the manager's license and
source permit another approach. No patch bytes are distributed by this write-up.

Before building that patch:

1. Identify the actual v1.1.0 executable: SHA-256, PE architecture, Steam build ID
   and OS. Determine whether native code can be read from the supplied file.
   If it is wrapped, follow [the runtime-observation route](https://github.com/cranebeaker/coop-anything/blob/main/playbook/reverse-engineering.md)
   without removing its protection.
2. Find and understand the current equivalents of all three sites and the
   recurring poke. Record original bytes and relevant caller/state transitions.
   A tiny three-byte pattern alone is not a unique or sufficient locator.
3. Reproduce the unmodified two-player restriction in an isolated test copy, then
   measure which constraint actually rejects the third/fourth participant.
4. Check the mode and stage selection paths, player-slot/ready/launch handling,
   actor spawning, extra-slot death handling, map changes and results. Do not
   assume that reaching a four-slot lobby solves these later stages.
5. Require an exact supported-build hash and original-byte guards before any
   write. Make changes reversible; refuse unsupported or ambiguous sites.
6. Validate four real clients with scripted in-game bots and state observations,
   including an unpatched control. AI-controlled extra bodies in one game
   process do not establish four-client networking.

A private v1.1.0.0 executable was subsequently supplied and inspected; the
static progress is recorded below. There is still no game asset installation or
connection to the owner's Windows machine. Live validation needs Windows runtime
observations and isolated real-client test installations.

## All-maps gate

The pinned manager contains these ten No Mercy stage labels. They are candidate
stage identities from the tool, not an enumeration of the v1.1.0 installation.
Check them against actual installed maps before finalizing the suite; add any
additional maps discovered. Missing assets or untested maps cannot count as a
complete all-maps pass.

| Trainer stage tag | Stage label | Four-client No Mercy outcome |
|---|---|---|
| S1210 | Rail Yard | NOT RUN |
| S1211 | Requiem for War | NOT RUN |
| S1212 | Urban Chaos | NOT RUN |
| S1213 | Mining the Depths | NOT RUN |
| S1214 | High Seas Fortress | NOT RUN |
| S1215 | Catacombs | NOT RUN |
| S1216 | Steel Beast | NOT RUN |
| S1217 | Rooftop | NOT RUN |
| S1218 | Creature Workshop | NOT RUN |
| S1219 | Liquid Fire | NOT RUN |

For each map, require actual No Mercy mode, four distinct live clients with
advancing input/heartbeat state, four controllable actors, enemy/combat
interaction for every participant, consistent match state, extra-slot death and
revive checks, completed results and a subsequent-round check. Record actual
score/timer behavior and any intentional trainer anti-cheat effects. Run normal
Mercenaries four-client coverage separately and preserve existing two-player
behavior.

No software was installed, no original input file or owner installation changed,
no account used and nothing published. A separate private candidate executable
was generated for static comparison; no executable was launched.


## Supplied v1.1.0.0 image: native port candidate

The private input is PE32/x86, preferred image base 0x400000, file/product version
1.1.0.0, size 20,914,128 bytes and image size 21,671,936. Its SHA-256 is
`b8bceaf09272d5f30b89940737763afa6dfb78647c81165af1aa8a10d0afeb35`.
The binary is private and is not included in any source archive.

Strong code matches were found at these RVAs:

| Role inferred from the surrounding native instructions | Supplied image RVA | File offset |
|---|---|---|
| Create-session count derived from menu field +0x178 | 0x612cdd | 0x6120dd |
| Initialize the slot count at object field +0x4c | 0x610b21 | 0x60ff21 |
| Assign distinct randomized slots using an occupied-slot mask | 0x610b3a | 0x60ff3a |

Each differs from the corresponding trainer target by 0x37c0. More importantly,
the actual old two-player instruction spans and surrounding code match the
expected operation. The original slot-selection block uses a two-value mask and
flips between two indices; the candidate uses the slot count as the modulus.
The candidate block's backward edge reaches the existing random-number call
setup at VA 0xa10b30 and its forward edge reaches VA 0xa10b55. These destinations
were checked in the supplied native image. Uniform address difference alone was
not accepted as proof.

The old trainer locations were also inspected in this image: they contain
unrelated instructions, so its old writes must not be applied there.

### Timer and pointer evidence

Following the manager's selected-game dispatch (RE6 ID 0x0b), poke 0x28 resolves
to a freeze operation with text `Timer frozen.` and a constant float 120.0.
It is **not a mode override**. The old RE6 pointer reader uses module RVA
0x13c549c for its cached game-info pointer, then derives the timer at -0x794.

The [public autosplitter](https://github.com/TheDementedSalad/RE6-Autosplitter/blob/main/Resident%20Evil%206%20Autosplitter.asl)
separately distinguishes English 1.0.6 and 1.1.0. It reports root RVAs 0x13cf49c
and 0x13cf454 for 1.1.0 and image size 21,671,936. Native references to these
current globals were also found in the supplied image. The collector reads these
roots and the proposed timer field only; **the timer displacement has not been
validated as a live v1.1.0 write target**.

### Separate local game project and verification

Original tools were prepared in a separate local game project, not embedded in
this hub. It contains a hash/expected-byte/context-guarded offline candidate
builder and a Windows process collector requesting read/query access only.
No game binary or Fluffy executable is in its shareable kit.

The offline candidate modifies instruction spans totalling 37 bytes at the
three sites (28 individual byte values change). Its SHA-256 is
`04a9ccffd76f65806c371c380c5e245125ca532a0725404d071ef317498667fa`.
The original input hash was rechecked and remained unchanged. The candidate is
incomplete: no live timer handling, game session or all-map result is validated.
It is not an installation or gameplay recommendation.

16 offline tests passed: 15 guard/output/observation tests and one using the
actual private image. They cover unknown/wrong/patched inputs, context and byte
mismatch, PE mapping and architecture, overlapping or invalid ranges, output
checksum, preserving input, refusing overwrite/in-place output/symlink escape,
and unknown/mutated/nonfinite observation handling. This was the initial
offline baseline; the subsequent read-only capture and extended 18-test suite
are recorded below. The ten-map No Mercy matrix remains entirely NOT RUN.

## First live baseline and native timer follow-up (2026-11-07)

### Observed

- A returned Windows report for the exact pinned executable contained six
  main/menu-screen samples. The collector successfully read the live image:
  all three relocated spans matched original instructions, none matched the
  candidate, and the three legacy locations matched disk during the capture.
  This is evidence about those samples, not all earlier trainer activity.
- Mode and legacy timer candidates were zero at the main menu. Neither is a
  live No Mercy validation. Heap addresses and the original report remain private.
- Current native function VA 0x55a610 takes its object through ECX/ESI, reads
  a float at +0x486c, subtracts the incoming time delta at VA 0x55a69b and
  stores the result at VA 0x55a6d6. It also accumulates time at +0x4874 and
  handles a state field at +0x4864. The bonus-time path at VA 0x5585f0 adds
  to +0x486c at VA 0x558681 and caps/stores the result. Initialization at
  VA 0x55cd44 stores the float returned by VA 0x551180 into +0x486c.
- The mode-object constructor stores its object in global VA 0x17cf454 at
  VA 0x55940b. The game-info constructor stores a separate object in global
  VA 0x17cf49c at VA 0x5682cb. The collector now reads both timer candidates
  independently; it does not depend on heap adjacency.

### Derived, still requiring live correlation

The +0x486c float has strong native countdown semantics. That is a better-founded
read-only diagnostic candidate than relying on a displacement from another
object. The two formulas happened to resolve to the same address in the first
capture, but that relationship is not assumed for other sessions. A live
No Mercy sample must correlate it with the displayed clock before considering
any freeze/write policy. The mode values and elapsed/state field interpretations
remain unverified in active No Mercy.

### Tools and checks

The schema-2 collector adds direct native-timer/elapsed/state observations,
address-equality reporting, a user-reported screen label and a bounded startup
delay so the game can regain focus. It still requests only read/query process
access; no game-memory writing API was added. Eighteen offline tests passed,
including the private executable fixture and independent/nonfinite pointer-path
cases. The additional fields have not yet run on Windows.

An attempted isolated native selector fixture did not execute: the cloud
rejected an ELF32 binary, and an ELF64 compatibility-segment attempt faulted.
No native-selector PASS is claimed; neither fixture is in the shareable kit.
No game binary was executed here. No software installed, original game input
changed, account used, environment settings changed or anything published.

## Clock-correlated solo No Mercy capture (2026-11-07)

### Observed

The schema-2 collector ran on the exact pinned build and returned twenty samples
labelled `no-mercy-running`. A separate confirmation matched the displayed clock
(about 0:52 to 0:33) and the Urban Chaos map. Private reports and heap addresses
remain in ignored local storage.

- Mode remained 80 (0x50); stage remained 1212, matching S1212 / Urban Chaos.
- The native countdown decreased from 52.47375 to 33.47399 seconds over
  19.011871 wall-clock seconds: a decrease of 18.99976349 seconds.
- The adjacent elapsed field increased by 19.00408936 seconds. Timer state
  remained zero. Both timer formulas resolved to the same address/value in
  all twenty samples; independent derivation is retained for future sessions.
- All three relocated code spans contained original instructions throughout.
  All three historical trainer locations matched disk throughout. No patch
  application or old-location write is observed in this capture.

### Derived

The direct mode-root +0x486c address is corroborated as the live countdown in
this solo No Mercy context. This closes the timer-identification gap for that
session; another identical capture is unnecessary. It does not validate writing
120.0, establish that a freeze is needed, or show four-player compatibility.

### Additional static startup evidence

The relocated slot initializer is method VA 0xa10a70, held at vtable
VA 0x15a60fc. Its constructor VA 0xa107c0 installs vtable 0x15a60e8; the factory
at VA 0xa131b0 constructs it with size 0x588. Static initialization at
VA 0x147be50 registers its type as `uIdStartUp34` through the name at
VA 0x15a616c and type object 0x17e60f0.

The startup routines at VAs 0xd2a4e0 and 0xd2aa50 instantiate that class through
factory calls at 0xd2a919 and 0xd2ae30. These same routines explicitly test
mode-object +0xac against 0x50 at 0xd2a9bd and 0xd2ae98 to select No Mercy-specific
continuations. This connects the slot initializer to the shared startup/menu
path that handles the observed No Mercy mode. It does not establish that any
particular online join or gameplay path executed in the returned solo capture.

### Remaining gate

The candidate still has only the three native code changes; timer policy is
unresolved. No write, extended lobby, four-client match, extra-slot death, score,
results or all-map case has passed. The Urban Chaos matrix row remains NOT RUN
for four-client QA. Controlled Windows execution with complete game assets and
real clients is unavailable in this cloud workspace, so automated in-game bot
verification cannot currently run. No further timer-only collection is needed.

No original install or save was modified, no software installed, no account used,
no environment draft updated, and nothing published.
