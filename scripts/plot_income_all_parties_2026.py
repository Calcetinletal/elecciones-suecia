"""Export all eight party vote shares versus district net income, with Spearman rho.

Run: .venv/bin/python scripts/plot_income_all_parties_2026.py
Uses only the stored, audited atlas snapshot; does not download or change source data.
"""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import math
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, FixedLocator, FixedFormatter, NullLocator

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'public/data/2026/joined_2026.csv'
PROVENANCE = ROOT / 'public/data/2026/income_provenance.json'
OUT = ROOT / 'reports/income-plots-2026'
STEM = 'income-all-parties-2026-English-v1-spearman'
CONFIG = [
    ('S', 'Social Democrats', '#c73646'),
    ('M', 'Moderates', '#2475b4'),
    ('SD', 'Sweden Democrats', '#d7a800'),
    ('V', 'Left Party', '#922b49'),
    ('C', 'Centre Party', '#368553'),
    ('KD', 'Christian Democrats', '#353b83'),
    ('L', 'Liberals', '#37a1c5'),
    ('MP', 'Greens', '#7b9e30'),
]
INK, MUTED = '#192f40', '#536877'

def average_ranks(values):
    _, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    return (np.cumsum(counts) - (counts - 1) / 2)[inverse]

def spearman(x, y):
    assert len(x) == len(y) >= 3 and np.ptp(x) > 0 and np.ptp(y) > 0
    return float(np.corrcoef(average_ranks(x), average_ranks(y))[0, 1])

def load_points():
    with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len({r['district_id'] for r in rows}) == len(rows)
    excluded, points = Counter(), []
    for row in rows:
        assert row['election_year'] == row['geometry_year'] == '2026'
        assert row['income_year'] == row['income_price_year'] == '2024'
        if row['election_reported'].lower() != 'true':
            excluded['unreported_election'] += 1
            continue
        if row['income_complete'].lower() != 'true':
            excluded['incomplete_income_estimate'] += 1
            continue
        try:
            income, people, total, valid = [float(row[k]) for k in
                ('mean_net_income', 'income_population', 'income_total_sek', 'valid_votes')]
            votes = {p: float(row['vote_' + p]) for p, _, _ in CONFIG}
        except (KeyError, ValueError):
            excluded['missing_value'] += 1
            continue
        if not all(math.isfinite(v) for v in (income, people, total, valid, *votes.values())) or people <= 0 or valid <= 0:
            excluded['invalid_value_or_denominator'] += 1
            continue
        # Never silently omit a nonpositive income merely to use a logarithmic axis.
        assert income > 0, 'Nonpositive income: switch to a linear axis before publishing.'
        assert abs(income - total / people) < .01
        assert all(0 <= v <= valid for v in votes.values())
        point = {'district_id': row['district_id'], 'district_name': row['district_name'],
                 'municipality_name': row['municipality_name'], 'mean_net_income_sek_per_year': income,
                 'income_year': 2024, 'income_price_year': 2024, 'election_year': 2026,
                 'valid_votes': int(valid)}
        for party, vote in votes.items():
            pct = 100 * vote / valid
            assert abs(pct - float(row['pct_' + party])) < .000001
            point['vote_' + party] = int(vote)
            point['pct_' + party] = pct
        points.append(point)
    assert len(points) == 6312, 'Review coverage changes before publishing a new snapshot.'
    return rows, points, dict(excluded)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, points, excluded = load_points()
    provenance = json.loads(PROVENANCE.read_text())
    assert provenance['reference_year'] == provenance['price_year'] == 2024
    x = np.array([p['mean_net_income_sek_per_year'] for p in points])
    summary = {
        'districts_in_source': len(rows), 'districts_plotted_per_panel': len(points), 'exclusions': excluded,
        'source_csv': str(SOURCE.relative_to(ROOT)), 'source_csv_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'income_provenance': provenance,
        'election_source_url': rows[0]['election_source_url'],
        'election_updated_at': sorted({r['election_updated_at'] for r in rows}),
        'election_status': dict(Counter(r['election_status'] for r in rows)),
        'x_definition': 'Estimated mean annual personal net income; SCB income population aged 20+, reference year 2024, SEK at 2024 prices.',
        'y_definition': '100 * party_votes / valid_votes',
        'x_display': 'Logarithmic, original SEK values labelled; all positive observed incomes included. No trimming or winsorisation.',
        'x_observed_range_sek': [float(x.min()), float(x.max())],
        'correlation': 'Spearman rho: Pearson correlation of average ranks, equal district weights, average ranks for ties; no significance tests.',
        'notes': ['Eight individually identified parliamentary parties in the atlas. Other parties are an aggregate category and are not an additional party panel.',
                  'Logarithmic display does not change Spearman rho; coefficients are computed from original income values.',
                  'Income is a spatial estimate, not salary or median income. Vote shares are observed provisional 2026 results.',
                  'District-level association does not identify individual voting behaviour or establish causality. Spatial dependence and estimation uncertainty remain.'],
        'parties': {},
    }
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 15,
        'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
        'axes.edgecolor': '#bbcad2', 'svg.fonttype': 'none', 'pdf.fonttype': 42})
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    fig.subplots_adjust(left=.055, right=.982, top=.802, bottom=.195, wspace=.19, hspace=.43)
    fig.set_facecolor('white')
    fig.text(.055, .957, 'Sweden 2026 | Income and the vote', fontsize=32, weight='bold')
    fig.text(.982, .959, 'Created by @Calcetinletal', ha='right', fontsize=16, weight='bold',
             color='#247b68', url='https://x.com/Calcetinletal')
    fig.text(.055, .918, 'Eight parties · 6,312 districts in every panel · one dot per district', fontsize=18, color=MUTED)
    fig.text(.055, .881, '2026 provisional votes  /  2024 estimated net income', fontsize=16, color=MUTED)
    fig.text(.982, .883, 'Spearman ρ · nonparametric', fontsize=16, weight='bold', ha='right', color='#247b68')
    titles = []
    for ax, (party, name, accent) in zip(axes.flat, CONFIG):
        y = np.array([p['pct_' + party] for p in points])
        rho = spearman(x, y)
        assert abs(rho - spearman(np.log(x), y)) < 1e-12
        ymax = min(100, max(5, math.ceil((float(y.max()) + .5) / 5) * 5))
        summary['parties'][party] = {'name': name, 'n': len(y), 'spearman_rho': rho,
            'pearson_r_raw_income_reference': float(np.corrcoef(x,y)[0,1]),
            'y_observed_range_pct': [float(y.min()), float(y.max())], 'y_axis_range_pct': [0, ymax]}
        ax.set_facecolor('#fafcfd')
        ax.set_axisbelow(True)
        ax.grid(axis='y', color='#dce5e9', linewidth=.8)
        ax.grid(axis='x', color='#e8eef1', linewidth=.6)
        scatter = ax.scatter(x, y, s=13, color=accent, alpha=.29, linewidths=0, zorder=3)
        assert len(scatter.get_offsets()) == len(points)
        ax.set_xscale('log')
        ax.set_xlim(140000, 2900000)
        assert ax.get_xlim()[0] <= x.min() <= x.max() <= ax.get_xlim()[1]
        ax.xaxis.set_major_locator(FixedLocator([150000,300000,600000,1200000,2400000]))
        ax.xaxis.set_major_formatter(FixedFormatter(['150k','300k','600k','1.2m','2.4m']))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_ylim(0, ymax)
        step = 10 if ymax >= 40 else 5
        ax.set_yticks(sorted(set([*range(0, ymax+1, step), ymax])))
        ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
        ax.tick_params(length=0, pad=7, labelsize=13)
        ax.spines[['top','right']].set_visible(False)
        text_color = '#846500' if party == 'SD' else '#24778f' if party == 'L' else accent
        titles.append(ax.text(0, 1.15, f'{party} · {name}', transform=ax.transAxes, fontsize=18, color=text_color, weight='bold'))
        ax.text(0, 1.055, f'Spearman ρ = {rho:+.3f}', transform=ax.transAxes, fontsize=15, color=text_color, weight='bold')
    fig.text(.012, .507, 'Vote share (% of valid votes)', rotation=90, va='center', fontsize=20)
    fig.text(.52, .140, 'Estimated mean annual net income (SEK per person)', ha='center', fontsize=21)
    fig.text(.52, .108, 'Log income axis · each tick doubles income · all districts shown · Y-axis ranges differ', ha='center', fontsize=15, color=MUTED)
    fig.text(.055, .065, 'Income: SCB full-year population aged 20+ · after tax, including capital income and transfers · 2024 prices.', fontsize=13, color=MUTED)
    fig.text(.055, .039, 'Sources: Valmyndigheten (14 Sep 2026 snapshot) + SCB · income spatially estimated on 2026 electoral boundaries.', fontsize=12, color=MUTED)
    fig.text(.055, .013, 'Equal district weights. Territorial associations do not establish causality or identify how individuals voted.', fontsize=12, color=MUTED)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for title, ax in zip(titles, axes.flat):
        assert title.get_window_extent(renderer).width <= ax.get_window_extent(renderer).width, 'Party title overflows panel.'
    fig.savefig(OUT / f'{STEM}.png', dpi=240)
    fig.savefig(OUT / f'{STEM}.pdf', metadata={'Title':'Sweden 2026 | Income and the vote','Author':'@Calcetinletal'})
    fig.savefig(OUT / f'{STEM}.svg', metadata={'Date':None,'Creator':'@Calcetinletal','Description':json.dumps(summary)})
    svg = OUT / f'{STEM}.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)
    with (OUT / f'{STEM}.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(points[0]),lineterminator='\n')
        writer.writeheader()
        writer.writerows(points)
    (OUT / f'{STEM}-statistics.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (OUT / 'README.md').write_text(f'''# Income and the vote: all eight parties, Sweden 2026

Created by @Calcetinletal. English 2 × 4 figure, PNG 4800 × 2880, vector PDF and SVG.
Run `.venv/bin/python scripts/plot_income_all_parties_2026.py` from the project root.
Dependencies are pinned in `reports/three-plots-2026/requirements.txt`.

Each panel includes all {len(points):,} districts with complete paired data; exclusions: {excluded}.
Parties: S, M, SD, V, C, KD, L and MP. The atlas groups remaining parties as “other”; this aggregate is not an individual party panel.
X: estimated mean annual personal net income in SEK, reference year 2024, constant 2024 prices.
The source population is SCB's full-year population aged 20+, with its source restrictions; see the income provenance in the statistics JSON.
Net income includes capital income and transfers after tax. It is not salary, median income or household-equivalised income.
Income is spatially estimated on 2026 electoral boundaries. Election results are the stored provisional 14 September 2026 snapshot.
Y: 100 × party votes / valid votes, checked against published percentage fields.

Spearman rho is calculated on the original observations, with average ranks for ties and equal district weights.
The income axis is logarithmic to show the full range without removing extreme values. This does not change Spearman rho.
All 6,312 districts are present in every panel; no trimming or winsorisation. Y limits follow each party's observed maximum.
No significance tests or regression lines are shown. Neither causality nor individual voting behaviour can be inferred from territorial associations.

The CSV contains exactly the plotted district values for all parties. The statistics JSON records sources, exclusions, definitions and coefficients.
Input SHA-256: {summary['source_csv_sha256']}.
''',encoding='utf-8')
    downloads=ROOT / 'public/reports'
    downloads.mkdir(parents=True,exist_ok=True)
    for suffix in ('.png','.pdf'):
        shutil.copyfile(OUT/f'{STEM}{suffix}',downloads/f'{STEM}{suffix}')
    print(json.dumps({p: {'rho':s['spearman_rho'],'n':s['n']} for p,s in summary['parties'].items()},indent=2))
    print(f'Created {STEM}: PNG, PDF, SVG, CSV and statistics JSON.')

if __name__ == '__main__':
    main()
