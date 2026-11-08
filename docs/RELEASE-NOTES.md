Fixes a menu-recognition defect: version 0.2.0 always read scene record zero.
The game selects among four records; this update follows that selection and
checks that it stays stable. This can explain "Not the observed menu scene"
on another PC even when the supported game is visibly at its main menu.
The scene check, inactive-session and no-player guards remain required.

Adds **Save diagnostics** to export a local read-only JSON report if a refusal
persists. It does not upload the report or change the running game.

The portable Windows launcher applies the **exact three-site patch** used in
the reported successful three-player standard Mercenaries and No Mercy sessions.
The tested runtime modules and patch bytes are preserved unchanged.

Download **RE6MercenariesPatch-0.2.1-windows-x64.zip**, extract it, start RE6
normally through Steam, and run `RE6MercenariesPatch.exe`. At the game's main
menu, click **Refresh → Apply**, then host a fresh lobby. Python and a copied
game folder are no longer required. Full instructions are in the ZIP's
`README.txt`.

The host applies the patch; friends initially join with unmodified clients.
Turn Fluffy's trainer off, restarting RE6 if it was active this session.
The mod manager itself can remain open. Closing RE6 discards the memory patch.

Compatibility is pinned to the original executable SHA-256
`b8bceaf09272d5f30b89940737763afa6dfb78647c81165af1aa8a10d0afeb35`.
Different regional or modified 1.1.0 executables are refused. Windows 10/11
64-bit is required by this packaged launcher.

Three-player gameplay is user-reported. Uploaded host captures independently
verify third-player admission. Six slots are configured, but four or more
real players and exhaustive map/round coverage remain unverified. No timer,
mode, save, game file or Steam-check patch has been added.

Automated checks cover the frozen source hashes, patch identity, Steam library
discovery, main-menu guards, apply/restore and rollback with synthetic memory,
and Windows executable/GUI startup. All 74 tests pass locally with private input;
public CI skips private/platform-specific tests. The owner confirms version 0.2.0
works on their normal Steam installation. The affected friend's first live run
with the corrected scene lookup is still pending.

The source kit actually used for the gameplay report is frozen at
[`v0.1.0-tested`](https://github.com/operatornorm/gigart/tree/v0.1.0-tested).
See [the evidence](https://github.com/operatornorm/gigart/blob/main/docs/THREE-PLAYER-RESULT.md)
and the release's `SHA256SUMS.txt` for download checksums.
