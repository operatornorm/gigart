# Candidate slot-selector execution check

On 2026-11-07, a new isolated fixture successfully executed the candidate's
exact **27-byte replacement selector** on the Linux x86-64 host. This advances
beyond disassembly and Python model checks, but is **not a Windows, full 32-bit
ABI or game test**.

## Method

`tests/test_selector_native.py` builds a small assembly fixture using the existing
system C compiler. No software is installed, and no game code is launched.
Only the original candidate replacement is executed, after matching an explicit
audited byte string. The test refuses a changed selector until the fixture is
reviewed. It does not execute bytes extracted from the private executable.

The selector uses instructions whose register-width encodings have the same
semantics in long mode. The fixture allocates its count-bearing object below
4 GiB, where its memory operand addresses the same location with 32- and 64-bit
addressing. It preserves the ten-byte retry-target spacing immediately before
the replacement: a five-byte ECX load and a five-byte relative call. The actual
game's RNG call is replaced by a bounded, scripted source of unsigned values.

The test leaves the original backward and forward branches inside the 27-byte
replacement unchanged. Its completion stub reports selected ECX and number of
RNG draws. The synthetic count-bearing object must remain byte-identical.

## Results

- **624 cases passed:** every occupancy mask for counts 2, 4 and 6, each possible
  starting residue, and the unsigned edge values `0xffffffff` and `0x80000000`.
  Every successful result was the first free residue in the supplied draw stream.
- Repeated occupied draws correctly returned to the RNG stub: twenty draws of
  occupied slot 0 followed by occupied slot 3 and free slot 4 consumed 22 draws
  and selected slot 4.
- A fully occupied six-slot mask exhausted the bounded synthetic draw stream
  without reporting success. The input object was unchanged in all cases.
- The complete repository suite passed **35 offline tests**, including the
  private-executable guard test, on this Linux host with its existing compiler.

## Limits and implications

The real selector has **no retry bound**. A full occupied mask or an RNG that
keeps producing occupied values can retry indefinitely. The fixture's limit
belongs to the synthetic RNG; it is not a fix or behavior added to the candidate.
The surrounding initializer starts with an empty mask and fills the configured
count, so normal sequential initialization should have a free slot at each
selection. That surrounding game execution has not been exercised here.

The fixture does not test the real RNG, surrounding native function, 32-bit
calling convention, online session, actor spawning, death/results handling or
timer policy. Earlier failed ELF32/compatibility-segment attempts remain failed
attempts; this narrower successful check does not replace them with a passing
full 32-bit test. Windows and non-x86-64 hosts skip the three fixture tests.

The candidate manifest and executable replacement bytes are unchanged. This
check supports the selector's local unsigned division, occupied-bit test and
retry branches, not a release-ready four-player No Mercy patch.
