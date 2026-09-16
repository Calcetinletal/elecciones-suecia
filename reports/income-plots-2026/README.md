# Income and the vote: all eight parties, Sweden 2026

Created by @Calcetinletal. English 2 × 4 figure, PNG 4800 × 2880, vector PDF and SVG.
Run `.venv/bin/python scripts/plot_income_all_parties_2026.py` from the project root.
Dependencies are pinned in `reports/three-plots-2026/requirements.txt`.

Each panel includes all 6,312 districts with complete paired data; exclusions: {}.
Parties: S, M, SD, V, C, KD, L and MP. The atlas groups remaining parties as “other”; this aggregate is not an individual party panel.
X: estimated mean annual personal net income in SEK, reference year 2024, constant 2024 prices.
The source population is SCB's full-year population aged 20+, with its source restrictions; see the income provenance in the statistics JSON.
Net income includes capital income and transfers after tax. It is not salary, median income or household-equivalised income.
Income is spatially estimated on 2026 electoral boundaries. Election results are the stored provisional 16 Sep 2026, 15:15 (Stockholm) snapshot.
Y: 100 × party votes / valid votes, checked against published percentage fields.

Spearman rho is calculated on the original observations, with average ranks for ties and equal district weights.
The income axis is logarithmic to show the full range without removing extreme values. This does not change Spearman rho.
All 6,312 districts are present in every panel; no trimming or winsorisation. Y limits follow each party's observed maximum.
No significance tests or regression lines are shown. Neither causality nor individual voting behaviour can be inferred from territorial associations.

The CSV contains exactly the plotted district values for all parties. The statistics JSON records sources, exclusions, definitions and coefficients.
Input SHA-256: ec0d764b416f961eaf175234e0c21e582d81529a2c035fb14ca83a092169ffb0.
