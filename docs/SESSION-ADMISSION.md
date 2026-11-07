# Session admission and player-object observations

Status, 2026-11-07: static tracing in the exact pinned v1.1.0.0 executable;
new collector fields now read successfully in a confirmed solo No Mercy capture.
Online-lobby values remain unverified. No new game
patch has been added, and no multiplayer or map has passed gameplay QA.

All addresses below are preferred virtual addresses in BH6.exe (base 0x400000),
not offsets to write into a running process. The executable's SHA-256 is
`b8bceaf09272d5f30b89940737763afa6dfb78647c81165af1aa8a10d0afeb35`.

## Observed in the native code

The host-side routine at **0x5197b0** prepares a response to a prospective
participant. Its successful path associates a peer with a slot and copies their
profile fields into the mode object. Relevant branches:

| Instructions | Observed behavior |
|---|---|
| 0x519823–0x51982e | If mode-object +0x74 is not 1, put `0xff` in the response slot byte |
| 0x519851–0x519870 | Call 0x5515a0; a negative result puts `0xfe` in that byte |
| 0x519875–0x5198a1 | Test a bit in the incoming capability/map mask; failure puts `0xfd` in that byte |
| 0x5198a6–0x519946 | Store the chosen index, associate it with the peer, copy profile fields, then set slot state to 1 |

These are static response values, not captured network rejection messages. The
map-mask interpretation is supported by the selected stage index (+0x3e50), the
No Mercy-specific shift of ten bits, and the matching client-side map-availability
test at 0x9757f6–0x975838. The bit tested is:

```text
selected_stage_index + (mode == 0x50 ? 10 : 0)
```

The actual incoming mask has not been observed. This is not evidence that the
owner or any particular peer lacks a map. A lobby-capacity change cannot by
itself satisfy the map check.

**0x5515a0** searches indices **0 through 5**, in ascending order. It returns the
first index whose slot kind is `1 + (argument_byte != 0)` and whose slot state is
zero. It returns -1 if no such entry exists. No two-slot bound appears in this
helper, and the three-site candidate does not alter it.

**0x551500** counts indices 0 through 5 for which kind is nonzero and state is
neither zero nor three. The collector calls these `native_counted_slot_indices`;
they are not a count of verified human clients. Kind/state values can represent
configuration, transitions and disconnected participants.

The mode object stores eight dwords per array, at 0x20-byte intervals:

| Offset | Purpose supported by code |
|---|---|
| +0x3efc | Slot states; host admission writes 1 at 0x519946 |
| +0x3f1c | Slot kinds inspected by the free-slot search |
| +0x3f3c | Randomized slot values written by the initializer containing the candidate |
| +0x3e54 | Create-path capacity candidate, written at 0xa12d1d |
| +0x3e50 | Selected stage index used by the admission map check |
| +0x4864 | Timer state, already observed in the solo baseline |
| +0x4868 | Timer slot mask tested at 0x55a80a |

The create path at 0xa12cd1 adds two (candidate: six) to menu field +0x178,
populates subsequent slot kinds and stores the result at mode +0x3e54. It is
an additive capacity change, not an unconditional assignment of six. The menu
initializer at 0xa10680 initializes that field to zero and its range field
(+0x190) to one. Actual menu selections and the advertised network capacity
remain unobserved. Do not infer a supported seven-player match from this formula.

At 0x55a7f0–0x55a819, a timer-state path examines **eight** entries, testing kind,
state 2 and a bit in mode +0x4868. Six-entry admission, eight stored entries and
this eight-entry timer path are distinct bounds. They do not justify raising
every loop bound or establish correct timer behavior with extra players.

## Separate player-object table

The type initializer at 0x1450ee0 names `sPlayer` and registers type metadata
0x17d0470. Its constructor path stores the manager instance at 0x17d0468
(0x593529), and destruction clears that global (0x5924af). The existing public
[autosplitter](https://github.com/TheDementedSalad/RE6-Autosplitter/blob/main/Resident%20Evil%206%20Autosplitter.asl)
also uses this root for v1.1.0, for a different field.

Getter **0x590b00** rejects indices outside 0..7 and returns the dword at
manager +0x24 + 4*index. Its callers check for null and invoke virtual methods on
the returned object (for example 0x4653cf–0x4653f0). This is a stronger
player-object presence signal than the lobby's reserved slots.

The collector reads only those eight table values, records present/absent/unknown,
counts distinct non-null addresses and flags duplicate entries. It does not
dereference the objects or save their addresses. A non-null pointer still does
not establish a live controllable actor, its owning peer, or a human client.
The mapping between these indices and randomized lobby slots is unverified.

## Collector behavior and next validation

`probe_windows.py` now writes **schema 3**, with `session` and `player_objects`
inside each sample. Existing timer and code-span observations remain available.
`session_probe.py` implements the bounded reads and the two native six-slot
predicates. It reads no peer names, account IDs, IP addresses or profile strings.

Unreadable/short reads remain unknown. Root pointers are rechecked after each
group of reads; if a root changes or becomes unreadable, that group's data is
discarded. An unchanged root does not make these reads atomic, and the two
groups are not a synchronized cross-object snapshot.

The new fields have synthetic-memory tests, including missing fields, duplicate
objects and changing roots. The complete suite has **32 passing offline tests**
when run with the private executable fixture. New live reads are now observed on
Windows in the solo context below. No new executable bytes were changed.

A useful next diagnostic is a normal, unmodified **Mercenaries two-player Create
Game lobby**, staying there throughout the capture without starting a match.
This verifies the newly traced lobby fields without assuming a
No Mercy online-lobby route that has not been demonstrated here. A separate
normal solo match capture has now established a one-object baseline below.
These are observation checks, not a four-person acceptance test. Keep the
existing trainer deactivated so stale legacy writes do not confound the result.
No repeat of timer identification is needed.

Remaining development gates are actual session capacity advertisement, controlled
third/fourth-client admission, slot-to-player-object mapping, No Mercy spawning,
timer policy, extra-player deaths/results and every map. This Linux workspace
does not have a complete game installation or Windows client execution access.

## Confirmed solo No Mercy capture

A returned schema-3 capture contains twenty samples over 19.0153 seconds. Its
command-line label says `mercenaries-lobby`, but the person collecting it
explicitly confirmed that **solo No Mercy was running**. The label is user-supplied
metadata and must not override that confirmation or the live readings.

All twenty samples contain:

| Observation | Value |
|---|---|
| Exact executable | Pinned v1.1.0.0 SHA-256 above |
| Mode and actual stage fields | 80 / 1212 (the previously correlated Urban Chaos stage) |
| Session-type candidate (+0x74) | 4 |
| Create-capacity candidate | 0 |
| Slot 0 | State 2, kind 3 |
| Slots 1–7 | State 0, kind 0 |
| Randomized slot entries | All zero |
| Six-slot helper's available entries | None of kind 1 or kind 2 |
| Player-object table | One non-null entry at index 0, seven null entries, no duplicates |
| Read groups | Root stable; all new fields readable |
| Current patch sites | Original instructions throughout |
| Historical trainer targets | Matched disk throughout |

The countdown changes from 108.83954 to 149.82019 seconds, with a positive
58.99982-second step between two approximately one-second samples. That is
consistent with a 60-second time bonus; its cause was not independently observed.
Elapsed time advances by 19.01643 seconds. This is not evidence of a timer freeze.

The recorded session-type value is different from the value 1 required by the
host admission path at 0x519823. This capture therefore cannot validate that
host path. Empty join-slot configuration and zero create capacity in a solo
session are not a reproduced online admission failure.

The lobby's stage-index candidate is zero even though the actual stage field
is 1212. Do not translate that zero into a map identity or assume create-lobby
fields are initialized meaningfully during a solo match. The new reads have
live observation evidence in this context; their online semantics, object
ownership and four-client behavior remain unverified.
