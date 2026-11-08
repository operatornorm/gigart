Removes screen/menu/scene requirements from **Apply** and **Restore**. The
returned diagnostic showed stable scene **904**, record index 0, an inactive
session and no player objects. Version 0.2.1 still refused it because it required
scene 1102. The new launcher checks session/player/slot state instead.

Download **RE6MercenariesPatch-0.2.2-windows-x64.zip**, extract it, start RE6
normally through Steam, and open `RE6MercenariesPatch.exe`. Outside any lobby or
round, click **Refresh → Apply**, then create a fresh Mercenaries lobby.
No particular screen or menu is required. Python and a copied game folder are
not needed. Full instructions are in the ZIP's `README.txt`.

All eight slot states must be zero; session/player data must be readable and
inactive. These checks run again while the process is suspended. Applying or
restoring inside an existing lobby or round is refused. This patch sets up the
next lobby; it does not resize an already-created lobby. Save diagnostics remains
available and exports a local read-only report without uploading anything.

The **exact three-site patch** and four original runtime files used for the
reported three-player standard Mercenaries and No Mercy sessions remain
unchanged. Exact executable/module identity, live code/context guards,
transaction readback, rollback and process resumption remain required.
No timer, mode, Steam-check, game-file or save changes have been added.

The host applies the patch; friends initially join with unmodified clients.
Turn Fluffy's trainer off, restarting RE6 if it was active this session. The mod
manager can remain open. Closing RE6 discards the memory patch.

Compatibility is pinned to executable SHA-256
`b8bceaf09272d5f30b89940737763afa6dfb78647c81165af1aa8a10d0afeb35`.
Other regional or modified files are refused. The package requires Windows 10/11
64-bit. Three-player gameplay is user-reported; uploaded host captures separately
verify third-player admission. Four or more actual players and exhaustive
map/round coverage remain unverified.

All **80 local tests** pass with private input. Tests reproduce the friend's
scene-904 inactive state and verify exact apply/restore output, refusal of active
or unknown sessions (including slot zero), and a session changing after Refresh.
Windows CI builds the executable and checks GUI startup without RE6; public
checks skip private/platform-specific tests. The owner confirmed 0.2.0 works on
their normal Steam installation. The affected friend's live application of this
new release remains pending.

The original source kit is frozen at
[`v0.1.0-tested`](https://github.com/operatornorm/gigart/tree/v0.1.0-tested).
See [the new guard and diagnostic evidence](https://github.com/operatornorm/gigart/blob/main/docs/MENU-STATE.md),
[gameplay evidence](https://github.com/operatornorm/gigart/blob/main/docs/THREE-PLAYER-RESULT.md),
and the release's `SHA256SUMS.txt` for download checksums.
