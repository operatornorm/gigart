# Reported three-player result — 8 November 2026

The host reports that three people using separate RE6 clients played both
standard Mercenaries and Mercenaries No Mercy together, without identifiable
timer, score, item or enemy-spawn issues. The host used the original native
trial kit. Joining clients were initially instructed to remain unmodified;
the gameplay report does not independently audit their installations.

## Captures

The two supplied read-only reports each contain six consistent samples:

| Capture UTC | Occupied host slots | Free configured partner slots | Live code |
|---|---|---|---|
| 7 November 2026, 23:52:31 | 0, 1 | 2, 3, 4, 5 | All three candidate spans |
| 7 November 2026, 23:53:32 | 0, 1, 2 | 3, 4, 5 | All three candidate spans |

Both have capacity 6, a permutation of indices 0–5, and unchanged historical
trainer targets. They record standard Mercenaries mode (30), menu scene 1102,
host session type 1, and no player objects. These are lobby captures: they
establish third-player admission, while the user's report supplies gameplay
evidence for both modes. Raw reports remain private.

Report SHA-256 values, in the table's order:

```
e1f907da931303e815ea0ed3690b01e28860562ffcc0bbeb373fe61e8e8b6dd3
5e225efb103fc91ea38bba152f1330efd24e30e75fbff0cf45a13f4bde256f18
```

## Exact tested source

The original distributed source archive came from commit
`ea19adebe0d2151fe81868f211ce8b9821d5c22b`, now tagged
[`v0.1.0-tested`](https://github.com/operatornorm/gigart/tree/v0.1.0-tested).
Its SHA-256 is
`3e4782499f9e31ee81da5b555f1d4872f59a32c767d46f4bca26c21a5ea55138`.

[tested-build.json](tested-build.json) pins the four runtime source files,
original game identity, complete three-site patch specification, and expected
candidate checksum. Later changes to evidence metadata do not change those
instructions. Automated checks enforce these pins for the normal-Steam wrapper.

## What is established

At least three players are supported in the reported sessions; another joining
experiment is unnecessary to establish that result. The code configures six
slots and selects among all six, and captured host memory confirms those slots.
This does not establish four, five or six working real clients. No exhaustive
map list, round duration, deaths/results or repeat-round coverage was supplied.
Those remain limits on the claim, not reasons to discard the three-player result.

No timer, mode or gameplay patch was added to obtain this result. The reported
working native timer is retained as-is.
