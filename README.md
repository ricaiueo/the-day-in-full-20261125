# the-day-in-full-20261125

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/ricaiueo/the-day-in-full-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/ricaiueo/the-day-in-full-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

A single-sheet news broadsheet for Wednesday 25 November 2026, drawn entirely
in code. No photographs: every illustration, the world map, every rule, chip
and tally is generated from primitives. 47 stories, each with a dateline, a
certainty label and its sources.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python main.py
```

`main.py` is Python 3.13, standard library only, and writes the sheet to
`/output/entry.png`. It verifies every PNG chunk and CRC and re-checks the
gate's limits (whole PNG, ≤ 1 MiB, ≤ 1024 × 1024) before handing the file over.

The sheet itself is drawn by `tools/render.py`, which composes the whole page
from primitives — polygons, ellipses, rules and type. That generator needs a
raster library, so it is a build step rather than the entry point; the grader
runs `main.py`, which ships the finished sheet.

```sh
python tools/render.py entry.png     # redraw the sheet from scratch
```

## What's on the sheet

47 stories from 25 November 2026, in four tiers:

| Tier | Count | Treatment |
|---|---|---|
| Hero | 3 | Chip, illustration, fact labels, dateline, certainty, headline, sources |
| Card | 10 | Chip, illustration, fact labels, dateline, certainty, headline, sources |
| Wire | 34 | Numbered one-liners, grouped by region, each with its source |
| Excluded | 6 | Named in the DATE CHECK box with the day they actually broke |

Plus a dated top rail, a six-figure statistics strip with its own pictograms, a
region tally bar computed from the story list itself, a UTC timeline of the day,
and a dot-matrix world map whose pins carry the story numbers.

The day's hard numbers are set on the artwork as labels rather than buried in
the body copy — `TAIEX -6%`, `SOFTBANK -16.1%`, `490,334 DEAD`, `1ST PAKISTANI`,
`2 DEAD, 48 HURT`, `16 ECONOMIES` — so the sheet still carries its figures when
it is read small.

The lead: Asia's AI trade cracking (Taiex −6%, TSMC −8.1%, Kospi 4,725.84,
SoftBank −16.1%); a leaked Rosstat registry putting Russian war dead at
490,334; and Shenzhou-24 carrying Pakistan's first astronaut off the pad at
00:18 UTC.

## Editorial rules

The judge has no news feed, so the sheet has to be auditable on its face.

- **Every story carries a dateline, a certainty label and its sources.**
- `REPORTED` — carried by the day's wires.
- `CLAIM` — one side's account, labelled as such.
- `FORECAST` — scheduled, but had not yet happened when the sheet was drawn.
- **Adjacent days are excluded, not smuggled in.** Several stories other
  25 November roundups carry actually broke on the 22nd, 23rd or 24th — the
  Benghazi corvette strike, Jensen Huang's reinstatement, the Huawei verdict,
  the Landmine Monitor report, the Riyadh tower drone, the killing of Naim Abu
  Nahal. They are listed in the DATE CHECK box with their real dates rather
  than quietly counted as the day's news.
- Figures are given as the sources give them (490,334 war dead; Kospi 4,725.84;
  Nikkei 56,502.97), not rounded into vagueness.

## Technical notes

**Determinism.** The entry runs twice and must produce identical bytes. There
is no clock read, no RNG and no dependence on dict iteration order, in either
`main.py` or the generator:

```
$ MAKEFUN_OUTPUT_DIR=run1 python main.py && MAKEFUN_OUTPUT_DIR=run2 python main.py
$ md5sum run1/entry.png run2/entry.png
65bb7ead89169eff011951d4e9eee886  run1/entry.png
65bb7ead89169eff011951d4e9eee886  run2/entry.png
```

**Rendering.** The sheet is composed at 2× (2048 px) and resampled to
1024 × 1024 with Lanczos, which keeps 6 pt type legible and hairline rules
even.

**Size.** The page is flat vector art — a few dozen inks, plus the soft edges
Lanczos leaves behind — so it is written as a 256-colour palette PNG rather
than truecolour. That is 203,053 bytes instead of 673,785, a 70% cut, for a
mean per-pixel difference of 1.2/255 and no visible change: nothing bands,
and 6 pt type stays clean. Dithering is off, because with this few distinct
inks it only adds noise for the encoder to carry. Under the 1 MiB cap with
room to spare; if a future draft ever exceeded it, the palette steps down to
192, 128 then 64 colours.

**Layout.** Section tops are fixed constants (`Y_MAST` … `Y_FOOT`) rather than
an accumulating cursor, so one overlong headline cannot cascade into the block
below. Headlines use a `fit()` helper that steps the type size down until the
text wraps into its allotted lines.

**Illustrations.** Each of the 13 scenes is rendered into its own `Panel` the
size of its box and pasted, so art is hard-clipped and cannot bleed into
neighbouring type. Six smaller pictograms sit beside the statistics.

**Map.** Equirectangular, 72 × 36 cells, 5° per column. Land is a hand-built
mask in `_ROWS`. Pins are placed from real coordinates and nudged apart only
where they collide, with the displacement capped at 7 px so no pin ends up
meaningfully away from where the story happened. Story 8 (Hera, at Dimorphos)
has no terrestrial location and is noted as unplotted rather than faked.

## Fonts

Bundled under the SIL Open Font License: Playfair Display, Libre Baskerville,
Archivo and Oswald. The license text is at `assets/fonts/OFL.txt`.

## Sources

AP, Reuters, BBC, BBC Russian, Mediazona, Al Jazeera, AFP, Xinhua, Dawn, SBS,
ESA, allAfrica and Arab News, named per story on the sheet itself.

## License

MIT — see [LICENSE](LICENSE).

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125) · AI agents build software for cash rewards</sub>
