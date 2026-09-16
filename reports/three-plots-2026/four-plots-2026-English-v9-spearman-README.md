# Sweden 2026: four-panel Spearman chart

Created by @Calcetinletal. Run `.venv/bin/python scripts/plot_four_panel_2026.py` from the project root.
Dependencies: `reports/three-plots-2026/requirements.txt`.

Each panel contains the same 6,312 districts. S = Social Democrats; V = Left Party; Greens = MP.
X is the estimated 2025 SCB rest-of-world + unknown birthplace share on 2026 electoral boundaries.
Russia and Turkey belong to Europe in this SCB classification. This measures birthplace, not citizenship.
Y is selected party votes divided by valid votes in the stored provisional 16 Sep 2026, 15:15 (Stockholm) snapshot.

Spearman rho is Pearson correlation of average ranks, with equal weight per district and average ranks for ties.
It measures monotonic association without assuming linearity or normality. No significance tests are calculated.
The dashed line is a separate OLS linear fit, not a Spearman fit. Y limits follow the maximum in each panel.
District association cannot identify individual votes or establish causality; spatial dependence and estimation uncertainty remain.

Input SHA-256: ec0d764b416f961eaf175234e0c21e582d81529a2c035fb14ca83a092169ffb0. Companion CSVs contain exactly the plotted points. Statistics JSON contains all four coefficients and definitions.
PNG: 3840 × 3000; PDF and SVG are vector formats.
