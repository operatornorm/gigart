# Three-client joining check

The current success target is **three real players in Mercenaries No Mercy**.
Four-player support and complete map coverage remain separate goals. The
candidate still configures six slots; no change to its bytes is needed to test
three participants.

So far, the original instructions, six-slot initialization and return to the
original instructions have each been observed on the supplied Windows build.
No extra peer has joined as part of those observations, and no round has run.

## First stage: standard Mercenaries lobby only

This stage isolates joining from No Mercy mode/spawning/timer behavior. It is
a joining diagnostic, not a gameplay acceptance test.

1. **Host:** use the isolated test copy, Fluffy's trainer deactivated. At the main
   menu, apply the candidate using the existing kit:

   ```powershell
   py -3 .\native_trial.py --pid (Get-Process BH6).Id --test-exe "D:\RE6-Test\BH6.exe" --apply
   ```

   Substitute the actual test-copy path. Create a fresh invite-only/private
   **standard Mercenaries duo** lobby. Leave No Mercy off for this stage.
2. **Joining clients:** use their own licensed Steam clients and matching v1.1.0
   build, with Fluffy's trainer deactivated. Start with their games unmodified;
   this first experiment applies the candidate to the host only. Historical
   trainer documentation supports host-only operation, but that remains an
   experimental assumption for this port.
3. Invite one participant normally through the game/Steam UI. Once their join
   attempt settles, keep both participants in the waiting lobby. Record whether
   the joining client also sees the session and whether any exact error appears.
4. On the host, run this read-only capture and keep the resulting JSON as the
   **two-client** report:

   ```powershell
   py -3 .\probe_windows.py --pid (Get-Process BH6).Id --context mercenaries-lobby --samples 6 --delay 10
   ```

5. Invite the next participant while the first stays connected. Keep all three
   clients in the waiting lobby; **do not start a round**. Run the same host
   capture command and identify that JSON as the **three-client** report.

Return both host captures with the observed joining outcomes. If the third
client is refused, capture the host while the first remains connected and quote
the third client's exact error. Do not repeatedly retry, change offsets or apply
patches to the joining clients to conceal that first failure.

Where a joining client already has Python 3.10+, an additional read-only capture
from that client can help separate host admission from client state. The
collector refuses unsupported executable hashes; do not relax that guard merely
because a title screen also says v1.1.0. No friend account ID, password or login
needs to be shared.

**Use `probe_windows.py` after peers join.** The existing `native_trial.py`
six-slot assessment intentionally checks an *empty* waiting lobby and will stop
matching when its partner entries become occupied. Its absence after joining
does not by itself mean a failed admission.

## How the result will be interpreted

- The host's six reserved/configured entries are not six connected clients.
- A second occupied slot plus confirmation from both clients establishes a
  two-client joining observation. The critical next step is the third client.
- Three occupied candidate slots alone are not proof of three independent
  logged-in peers. Match the host report with the participants' observed join
  outcomes and client-side reports when available.
- Player-object entries may stay null in the waiting lobby. That does not
  refute admission, and non-null entries later would not by themselves prove
  controllable actors or successful combat.
- Passing this joining stage does not establish No Mercy gameplay or map
  coverage. Subsequent work must verify mode selection, spawning, synchronization,
  timer policy, deaths/results and another round before declaring three-player
  No Mercy successful. Automated gameplay QA is separately unrun.

After the joining captures, leave the lobby and restore at the main menu, or
close the test game to discard process-memory changes. See
[the apply/restore instructions](LOBBY-TRIAL.md).

## Static matchmaking check completed while awaiting clients

The game imports `SteamMatchmaking` through IAT VA 0x1502484. At 0x419284–0x419296
it calls the returned interface's vtable entry +0x34, pushing the object field
at +0xad10 and then the constant 2. The published
[ISteamMatchmaking009 declaration](https://github.com/rlabrecque/Steamworks.NET/blob/ea51b029a5dbcb47a99d3c1fac930b811672ed32/CodeGen/steam/isteammatchmaking.h)
places `CreateLobby(ELobbyType, int cMaxMembers)` at that entry. Its enum gives
2 as `k_ELobbyTypePublic`.

Under that interface layout, the nearby **constant 2 is a lobby type**, not a
two-player member limit. The maximum-member argument is loaded dynamically from
+0xad10. Initialization at 0x419091 stores that field from task +0x2c (or zero
when the related task count is zero). This does not establish which task values
the candidate actually supplied during the returned lobby snapshot.

The shipped steam_api.dll has not been inspected here, and no live Steam call
was captured. This is a static interface-layout inference, not a measured Steam
member limit or proof of third-client compatibility. No additional patch is
justified by this trace, and the original three-site candidate remains unchanged.
