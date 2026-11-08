# Session checks without screen restrictions — launcher 0.2.2

Version 0.2.2 applies/restores independently of the current screen, menu or scene
ID. It requires a readable inactive session and no active player objects or
occupied slots. Existing lobbies must be left and created afresh: these code
patches affect lobby initialization, not the capacity of an existing session.

## Returned diagnostic

The affected friend reports the refusal while at the game's menus. Their
version-0.2.1 diagnostic records:

| Observation | Value |
|---|---|
| Supported executable and live code | Exact pinned build; all three original contexts |
| Historical trainer targets | Match disk |
| Selected record | 0, stable |
| Selected and record-zero scene | 904 |
| Session root | Stable |
| Session type | 0 |
| All eight slot states | 0 |
| Player-object table | Stable; all eight entries absent |

The previous correction to indexed scene reading did **not** resolve this case:
record zero was selected and stable. Requiring scene 1102 was too restrictive.
The diagnostic does not establish scene 904 as a universal menu ID; no scene
allowlist is used in the new launcher. The raw report remains private; SHA-256:

`037608fa4d2e0e475f048dabcaf964ed19be1278578284d1ec9734dfbe7f4fc6`

## Apply and Restore conditions

The normal-Steam wrapper now checks:

- A stable, readable session root and session type 0 or 4, preserving the
  previously accepted inactive-session types.
- All eight slot states are readable and zero. This includes slot zero, so a
  solo round before player creation is not accepted just because peers are absent.
- The player-manager root is readable: either explicitly null, or a valid
  pointer with a stable, completely empty eight-entry player-object table.
  Unknown, invalid or inconsistent player reads are refused.

These conditions are rechecked while every game thread is suspended, before
building and committing the original guarded transaction. Refresh is read-only;
its result alone never authorizes a later write. Exact disk/module identity,
patch contexts, historical trainer checks, readback and rollback remain in force.

Scene data is diagnostic only. A different scene, unreadable game-info root or
changing scene-record index does not block a separately verified inactive
session. This does not enable applying/restoring inside a lobby or round, and
does not resize a lobby already created before application.

The four original runtime files and all three patch records remain unchanged.
The historical `native_trial.py` still preserves its original menu-only policy;
use the normal-Steam launcher for the new policy.

## Diagnostic scene reading

The native getter at preferred VA **0x455380** in the pinned executable reads:

```text
info = read_u32(BH6.exe + 0x13cf49c)
index = read_u32(info + 0x20)
scene = read_u32(info + 0x412a4 + index * 0x3ce4)
```

The constructor at **0x5682a8–0x5682c1** constructs four records; the bounded
reader accepts indices 0–3 and rechecks the root and index. Setter
**0x46495c–0x464969** and initialization **0xd29f3b–0xd29f44** use the same
indexed layout. This correction from 0.2.1 is retained for accurate diagnostics,
without making the scene value a patching prerequisite.

Save diagnostics exports a new local JSON file through the read-only backend.
It does not suspend/write the game, upload anything, overwrite an existing file,
or read peer names, account IDs or profiles.

## Validation

All **80 tests** pass locally with the private executable. Regression fixtures
reproduce the returned scene-904/inactive-session state and verify exact
apply/restore bytes. Unreadable scene data is accepted when session/player
checks pass. Active host/join sessions, player objects, occupied slot zero,
unknown reads and a session becoming active after Refresh are refused before
any write. Transaction failure still rolls back and resumes the process.

Private-input tests verify the executable and native scene-layout instructions.
Public CI skips those two tests; Windows additionally skips three Linux-native
selector tests and the POSIX symlink test. Windows CI builds the executable and
checks GUI startup without RE6. This release's live application on the affected
PC remains to be confirmed.
