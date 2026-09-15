# S + V + G and residents born outside Europe, 2026

Standalone chart, separate from the web app. PNG at 200 dpi and vector SVG.
Created by @Calcetinletal.

- S: Social Democrats · V: Left Party · G: Green Party (MP).
- 6312 of 6312 districts included; 0 excluded.
- X: 100 × estimated residents in SCB's rest-of-world + unknown-birthplace category / population from the same SCB table.
- Y: 100 * (vote_S + vote_V + vote_MP) / valid_votes, calculated from counts.
- Pearson r: 0.733767; Spearman rho: 0.669250. Each district has equal weight.
- Estimated 2025 population on 2026 district boundaries. Stored provisional election snapshot: 14 September 2026.
- SCB includes Russia and Turkey in Europe. The plotted category includes unknown birthplace and does not measure citizenship.
- District association does not establish causality or identify individuals' votes.

The CSV contains exactly the plotted points. `SVG-2026-Calcetinletal-en-v4-statistics.json` records definitions, exclusions, sources and the input SHA-256.

## Reproduce from the project root

```sh
.venv/bin/pip install -r reports/three-plots-2026/requirements.txt
.venv/bin/python scripts/plot_party_combinations_2026.py --combination SVG
```

Input: `public/data/2026/joined_2026.csv`. The builder validates unique IDs, reference years, denominators and agreement with published percentages before plotting.
