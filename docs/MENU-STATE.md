# Selected scene record correction — launcher 0.2.1

The owner confirms that the normal-Steam launcher works on their PC. Another
person using the supported executable reports "Original game code. Not the
observed menu scene" at Play Game / Extra Content / Mercenaries screens.
With RE6 closed, the launcher correctly asks them to start the game.

"Original game code" means Steam path, exact disk hash, live module identity,
all three original patch contexts and historical trainer targets passed their
checks. The later refusal concerns menu recognition. No diagnostic capture from
the affected PC has yet established its actual scene or selected record index.

## Native evidence

Addresses below are preferred virtual addresses in the exact pinned executable.
The native getter at **0x455380** is:

```asm
mov eax, [ecx + 0x20]
imul eax, eax, 0x3ce4
mov eax, [eax + ecx + 0x412a4]
ret
```

With `info = [BH6.exe + 0x13cf49c]`, the scene is therefore:

```text
index = read_u32(info + 0x20)
scene = read_u32(info + 0x412a4 + index * 0x3ce4)
```

The constructor at **0x5682a8–0x5682c1** constructs four records beginning at
`info + 0x3f798`, advancing by `0x3ce4`; the loop counter starts at 3 and
continues through zero. The launcher bounds the selected index to **0–3**.
The stage setter at **0x46495c–0x464969** and scene initialization at
**0xd29f3b–0xd29f44** use the same index and stride. No assumption about which
controller, account, save or option determines that index is needed.

The original collector read `info + 0x412a4` without the index. That agrees with
the native getter only when index is zero (or records happen to agree). This is
a confirmed source defect and a plausible cause of the friend's refusal. Its
role on that particular PC still needs confirmation with the updated launcher.

## Change and retained guards

`menu_state.py` implements bounded reads with rechecks of both root and index.
Unreadable fields, invalid indices or a changed selection yield an unknown scene;
the launcher refuses Apply and Restore. It never falls back to record zero.
The existing scene value **1102**, inactive-session requirement, absent-player
checks, suspended write transaction, code guards and rollback remain in force.
The corrected scene read also runs again while the process is suspended.

The four original runtime files and all three patch records remain unchanged.
`steam_patch.py` uses a wrapper snapshot containing the selected scene, while
retaining the legacy observation separately for diagnosis. The historical kit's
`probe_windows.py` and `native_trial.py` continue to preserve their exact tested
source; use the new launcher for the corrected menu lookup.

**Save diagnostics** opens the read-only backend and exports a new JSON file
chosen by the user. It includes the selected index, selected scene, record-zero
scene, stability flags, code observations and existing bounded session/player
observations. It neither suspends nor writes the game, uploads anything, nor
overwrites an existing file. No peer names, account IDs or profiles are read.

## Validation

The regression fixture accepts a selected nonzero record containing menu scene
1102 even when record zero is stale. It also refuses a selected gameplay scene
1212 when record zero still contains 1102, and verifies zero writes on refusal.
Invalid/short reads, root/index changes, all four indices, diagnostics export,
and the exact patched output are covered. A private-input test verifies the
getter and constructor instruction bytes against the pinned executable.

All **74 local tests** pass with the private input. Public builds skip the two
private-input tests; Windows additionally skips the three Linux-native selector
checks and POSIX symlink test. Windows CI builds the executable and checks GUI
startup without RE6. The affected friend's first live run remains unverified.
