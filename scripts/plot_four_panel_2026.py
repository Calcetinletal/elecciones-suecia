"""Create a compact 2x2 Spearman figure directly from the atlas district data.
Run: .venv/bin/python scripts/plot_four_panel_2026.py
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, MultipleLocator

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/three-plots-2026'
STEM = 'four-plots-2026-English-v8-spearman'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT / 'public/data/2026/joined_2026.csv'
with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
    source_rows = list(csv.DictReader(stream))
assert len({r['district_id'] for r in source_rows}) == len(source_rows)

def average_ranks(values):
    _, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    return (np.cumsum(counts) - (counts - 1) / 2)[inverse]

PARTY_IDS = {'S': ['S'], 'V': ['V'], 'SV': ['S', 'V'], 'SVG': ['S', 'V', 'MP']}

def panel_data(code):
    points = []
    for row in source_rows:
        assert row['election_year'] == row['geometry_year'] == '2026'
        assert row['birth_regions_year'] == '2025'
        if row['election_reported'].lower() != 'true' or row['birth_regions_complete'].lower() != 'true':
            continue
        try:
            valid, born, population = [float(row[k]) for k in ('valid_votes', 'born_rest_world_unknown_count', 'birth_regions_population')]
            votes = sum(float(row['vote_' + p]) for p in PARTY_IDS[code])
        except (ValueError, KeyError):
            continue
        if not all(math.isfinite(v) for v in (valid, born, population, votes)) or valid <= 0 or population <= 0:
            continue
        assert 0 <= votes <= valid and 0 <= born <= population
        x, y = 100 * born / population, 100 * votes / valid
        assert abs(x - float(row['born_rest_world_unknown_pct'])) < .00002
        assert abs(y - sum(float(row['pct_' + p]) for p in PARTY_IDS[code])) < .000003
        points.append({'district_id': row['district_id'], 'district_name': row['district_name'],
                       'rest_world_unknown_pct': x, 'selected_vote_pct': y})
    return points
INK, MUTED = '#192F40', '#536877'
CONFIG = [
    ('S', 'S · Social Democrats', '#CF344B'),
    ('V', 'V · Left Party', '#9D285B'),
    ('SV', 'S + V', '#AB315F'),
    ('SVG', 'S + V + Greens (MP)', '#247B68'),
]
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 15,
    'text.color': INK, 'axes.labelcolor': INK,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'axes.edgecolor': '#BBCAD2', 'svg.fonttype': 'none', 'pdf.fonttype': 42,
})
fig, axes = plt.subplots(2, 2, figsize=(16, 12.5))
fig.subplots_adjust(left=.073, right=.977, bottom=.188, top=.870, wspace=.145, hspace=.255)
fig.set_facecolor('white')
fig.text(.073, .948, 'Sweden 2026 | Votes and birthplace', fontsize=29, weight='bold')
fig.text(.073, .912, '6,312 districts · one dot per district · provisional votes · estimated 2025 population', fontsize=16, color=MUTED)
fig.text(.977, .951, 'Created by @Calcetinletal', ha='right', fontsize=14, weight='bold', color='#247B68', url='https://x.com/Calcetinletal')
source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
summaries = {}
reference_ids = None
for ax, (code, label, accent) in zip(axes.flat, CONFIG):
    rows = panel_data(code)
    ids = [row['district_id'] for row in rows]
    assert len(set(ids)) == len(ids) == 6312
    if reference_ids is None:
        reference_ids = ids
    assert reference_ids == ids
    x = np.array([float(row['rest_world_unknown_pct']) for row in rows])
    y = np.array([float(row['selected_vote_pct']) for row in rows])
    pearson = float(np.corrcoef(x, y)[0, 1])
    rho = float(np.corrcoef(average_ranks(x), average_ranks(y))[0, 1])
    slope, intercept = map(float, np.polyfit(x, y, 1))
    ymax = min(100, max(5, math.ceil((float(y.max()) + .5) / 5) * 5))
    stats = {'districts_plotted': len(rows), 'districts_excluded': len(source_rows)-len(rows),
             'primary_correlation': 'Spearman rho (nonparametric, average ranks for ties)',
             'spearman_rho_equal_district_weight': rho, 'pearson_r_equal_district_weight': pearson,
             'ols_intercept': intercept, 'ols_slope_pp_per_pp': slope, 'y_axis_limits': [0, ymax],
             'source_csv_sha256': source_sha, 'source_csv': str(SOURCE.relative_to(ROOT)),
             'party_codes': PARTY_IDS[code], 'population_year': 2025, 'election_year': 2026,
             'x_definition': '100 * born_rest_world_unknown_count / birth_regions_population',
             'y_definition': '100 * sum(selected party vote counts) / valid_votes',
             'notes': 'Equal district weights; no significance tests. Dashed line is OLS, not a Spearman fit. Spatial estimates; no individual-vote inference.'}
    with (OUT / f'{STEM}-{code}.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    assert 0 <= y.min() <= y.max() <= ymax and 0 <= x.min() <= x.max() <= 70
    ax.set_facecolor('#FAFCFD')
    ax.set_axisbelow(True)
    ax.grid(axis='y', color='#DDE5E9', linewidth=.9)
    ax.grid(axis='x', color='#EAF0F3', linewidth=.7)
    scatter = ax.scatter(x, y, s=20, color=accent, alpha=.34, linewidths=0, zorder=3)
    assert len(scatter.get_offsets()) == 6312
    fit_x = np.array([x.min(), x.max()])
    ax.plot(fit_x, stats['ols_intercept'] + stats['ols_slope_pp_per_pp'] * fit_x,
            color=INK, linewidth=1.8, linestyle=(0, (5, 4)), zorder=4)
    ax.set_xlim(0, 70)
    ax.set_ylim(0, ymax)
    step = 10 if ymax <= 70 else 20
    ax.set_yticks(sorted(set(list(range(0, ymax + 1, step)) + [ymax])))
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.tick_params(length=0, pad=7, labelsize=14)
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_title(label, loc='left', fontsize=20, weight='bold', color=accent, pad=12)
    ax.set_title(f'Spearman ρ = {rho:.3f}', loc='right', fontsize=15, weight='bold', color=accent, pad=12)
    summaries[code] = stats
fig.text(.015, .525, 'Vote share (% of valid votes)', va='center', rotation=90, fontsize=19, weight='medium')
fig.text(.525, .132, 'Residents born outside Europe* (% of district population)', ha='center', fontsize=19, weight='medium')
fig.text(.073, .093, '* Africa, Asia, the Americas and Oceania + unknown birthplace. SCB includes Russia and Turkey in Europe.', fontsize=12.5, color=MUTED)
fig.text(.073, .064, 'ρ: nonparametric rank correlation · equal district weights · dashed line: OLS fit · Y-axis ranges differ.', fontsize=12.5, color=MUTED)
fig.text(.073, .035, 'Sources: Valmyndigheten + SCB · votes: 14 Sep 2026 · population: 31 Dec 2025, estimated on 2026 boundaries.', fontsize=11, color=MUTED)
fig.text(.073, .014, 'Birthplace, not citizenship. District association does not identify how individuals voted.', fontsize=11, color=MUTED)
fig.savefig(OUT / f'{STEM}.png', dpi=240)
fig.savefig(OUT / f'{STEM}.svg', metadata={'Date': None, 'Creator': '@Calcetinletal', 'Description': json.dumps(summaries)})
fig.savefig(OUT / f'{STEM}.pdf', metadata={'Title': 'Sweden 2026 | Votes and birthplace', 'Author': '@Calcetinletal'})
plt.close(fig)
(OUT / f'{STEM}-statistics.json').write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding='utf-8')
(OUT / f'{STEM}-README.md').write_text(f'''# Sweden 2026: four-panel Spearman chart

Created by @Calcetinletal. Run `.venv/bin/python scripts/plot_four_panel_2026.py` from the project root.
Dependencies: `reports/three-plots-2026/requirements.txt`.

Each panel contains the same 6,312 districts. S = Social Democrats; V = Left Party; Greens = MP.
X is the estimated 2025 SCB rest-of-world + unknown birthplace share on 2026 electoral boundaries.
Russia and Turkey belong to Europe in this SCB classification. This measures birthplace, not citizenship.
Y is selected party votes divided by valid votes in the stored provisional 14 September 2026 snapshot.

Spearman rho is Pearson correlation of average ranks, with equal weight per district and average ranks for ties.
It measures monotonic association without assuming linearity or normality. No significance tests are calculated.
The dashed line is a separate OLS linear fit, not a Spearman fit. Y limits follow the maximum in each panel.
District association cannot identify individual votes or establish causality; spatial dependence and estimation uncertainty remain.

Input SHA-256: {source_sha}. Companion CSVs contain exactly the plotted points. Statistics JSON contains all four coefficients and definitions.
PNG: 3840 × 3000; PDF and SVG are vector formats.
''', encoding='utf-8')
print(json.dumps({code: {'rho': s['spearman_rho_equal_district_weight'], 'n': s['districts_plotted']} for code,s in summaries.items()}, indent=2))
downloads = ROOT / 'public/reports'
downloads.mkdir(parents=True, exist_ok=True)
for suffix in ('.png', '.pdf'):
    shutil.copyfile(OUT / f'{STEM}{suffix}', downloads / f'{STEM}{suffix}')
print(f'Created {STEM}: PNG 3840 x 3000, vector SVG and PDF. Verified all 6,312 districts in each panel and axis limits.')
