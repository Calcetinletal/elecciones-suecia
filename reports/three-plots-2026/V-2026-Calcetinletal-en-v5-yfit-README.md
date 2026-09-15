# V and residents born outside Europe, 2026

Standalone chart, separate from the web app. PNG at 200 dpi and vector SVG.
Created by @Calcetinletal.

- V: Left Party.
- 6312 of 6312 districts included; 0 excluded.
- X: 100 × estimated residents in SCB's rest-of-world + unknown-birthplace category / population from the same SCB table.
- Y: 100 * (vote_V) / valid_votes, calculated from counts.
- Y-axis runs from 0 to 65%, rounded up to the next 5 percentage points with at least 0.5 pp of headroom; no observations are removed. Scales differ between party combinations.
- Pearson r: 0.832461; Spearman rho: 0.784773. Each district has equal weight.
- Estimated 2025 population on 2026 district boundaries. Stored provisional election snapshot: 14 September 2026.
- SCB includes Russia and Turkey in Europe. The plotted category includes unknown birthplace and does not measure citizenship.
- District association does not establish causality or identify individuals' votes.

The CSV contains exactly the plotted points. `V-2026-Calcetinletal-en-v5-yfit-statistics.json` records definitions, exclusions, sources and the input SHA-256.

## Reproduce from the project root

```sh
.venv/bin/pip install -r reports/three-plots-2026/requirements.txt
.venv/bin/python scripts/plot_party_combinations_2026.py --combination V
```

Input: `public/data/2026/joined_2026.csv`. The builder validates unique IDs, reference years, denominators and agreement with published percentages before plotting.

