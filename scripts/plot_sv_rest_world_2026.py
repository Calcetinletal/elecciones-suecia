"""Export a standalone 2026 district scatterplot; does not modify the web app.
Run: .venv/bin/python scripts/plot_sv_rest_world_2026.py
"""
from pathlib import Path
import csv
import hashlib
import importlib.metadata
import json
import math
from collections import Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, PercentFormatter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'public/data/2026/joined_2026.csv'
OUT = ROOT / 'reports/sv-resto-mundo-2026'
OUT.mkdir(parents=True, exist_ok=True)
STEM = 'sv-resto-mundo-distritos-2026'

def finite_number(row, key):
    try:
        v = float(row[key])
        return v if math.isfinite(v) else None
    except (KeyError, ValueError, TypeError):
        return None

with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
    source_rows = list(csv.DictReader(stream))
assert len({r['district_id'] for r in source_rows}) == len(source_rows), 'Duplicate district IDs'
points, excluded = [], Counter()
for row in source_rows:
    assert row['election_year'] == row['geometry_year'] == '2026'
    assert row['birth_regions_year'] == '2025'
    assert len(row['district_id']) == 8 and row['district_id'].isdigit()
    if row['election_reported'].lower() != 'true':
        excluded['unreported'] += 1
        continue
    votes_s, votes_v, valid, born, population = [finite_number(row, k) for k in (
        'vote_S', 'vote_V', 'valid_votes', 'born_rest_world_unknown_count', 'birth_regions_population')]
    if any(v is None for v in (votes_s, votes_v, valid, born, population)) or valid <= 0 or population <= 0:
        excluded['missing_or_invalid_denominator'] += 1
        continue
    if row['birth_regions_complete'].lower() != 'true':
        excluded['incomplete_birth_estimate'] += 1
        continue
    assert 0 <= votes_s + votes_v <= valid and 0 <= born <= population
    x, y = 100 * born / population, 100 * (votes_s + votes_v) / valid
    # Cross-check the published percentage fields; CSV counts have six decimal places.
    assert abs(x - float(row['born_rest_world_unknown_pct'])) < 0.00002
    assert abs(y - float(row['pct_S']) - float(row['pct_V'])) < 0.000002
    points.append({
        'district_id': row['district_id'], 'district_name': row['district_name'],
        'municipality_name': row['municipality_name'], 'county_name': row['county_name'],
        'election_year': 2026, 'population_year': 2025,
        'rest_world_unknown_pct': x, 'sv_vote_pct': y,
        'votes_s': int(votes_s), 'votes_v': int(votes_v), 'valid_votes': int(valid),
        'rest_world_unknown_residents_estimated': born, 'birth_population_estimated': population,
        'coverage_quality': row['coverage_quality'], 'election_status': row['election_status'],
    })
assert len(points) >= 3
x = np.array([r['rest_world_unknown_pct'] for r in points])
y = np.array([r['sv_vote_pct'] for r in points])
assert np.std(x) > 0 and np.std(y) > 0
r = float(np.corrcoef(x, y)[0, 1])

def average_ranks(values):
    _, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    ends = np.cumsum(counts)
    return (ends - (counts - 1) / 2)[inverse]

rho = float(np.corrcoef(average_ranks(x), average_ranks(y))[0, 1])
slope, intercept = map(float, np.polyfit(x, y, 1))
source_times = sorted({row['election_updated_at'] for row in source_rows})
summary = {
    'districts_in_source': len(source_rows), 'districts_plotted': len(points),
    'excluded': dict(excluded), 'pearson_r_equal_district_weight': r,
    'spearman_rho_equal_district_weight': rho,
    'ols_slope_pp_per_pp': slope, 'ols_intercept': intercept,
    'x_min_max': [float(x.min()), float(x.max())], 'y_min_max': [float(y.min()), float(y.max())],
    'coverage_quality_counts': dict(Counter(p['coverage_quality'] for p in points)),
    'source_updated_at': source_times, 'source_csv': str(SOURCE.relative_to(ROOT)),
    'source_csv_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'x_definition': '100 * born_rest_world_unknown_count / birth_regions_population',
    'y_definition': '100 * (vote_S + vote_V) / valid_votes',
    'population_reference_date': '2025-12-31', 'district_geometry_year': 2026,
    'election_status_counts': dict(Counter(p['election_status'] for p in points)),
    'notes': [
        'Each point is one territorial district. All districts with complete paired values are included, irrespective of coverage quality.',
        'The x variable is SCB rest of world plus unknown birthplace. Europe includes Russia and Turkey in this classification.',
        'Demography is a population-grid spatial estimate on 2026 district boundaries, using SCB 2025 data with CKM disclosure control.',
        'Election results are the stored provisional snapshot, not a fresh live download. Collection districts are excluded.',
        'Correlations are unweighted across districts and descriptive, without causal or individual-vote attribution. Spatial dependence and estimation error remain.',
    ],
    'sources': {'elections': source_rows[0]['election_source_url'], 'population': source_rows[0]['birth_regions_source_url']},
}
(OUT / 'statistics.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
with (OUT / (STEM + '.csv')).open('w', encoding='utf-8-sig', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(points[0]))
    writer.writeheader()
    writer.writerows(points)

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 11, 'svg.fonttype': 'none',
    'axes.labelcolor': '#22344b', 'text.color': '#172b43',
    'xtick.color': '#53677c', 'ytick.color': '#53677c',
    'axes.edgecolor': '#b9c7d3', 'axes.linewidth': 0.8,
})
fig, ax = plt.subplots(figsize=(12.5, 8.6), facecolor='white')
fig.subplots_adjust(left=0.09, right=0.966, bottom=0.245, top=0.775)
ax.set_facecolor('#f7f9fc')
ax.set_axisbelow(True)
ax.grid(color='#dfe6ef', linewidth=0.75)
ax.scatter(x, y, s=15, c='#be3157', alpha=0.32, edgecolors='none', zorder=3)
xmax = min(100, max(10, math.ceil((float(x.max()) + 2) / 10) * 10))
ax.set_xlim(0, xmax)
ax.set_ylim(0, 100)
ax.xaxis.set_major_locator(MultipleLocator(10))
ax.yaxis.set_major_locator(MultipleLocator(20))
ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
ax.spines[['top', 'right']].set_visible(False)
ax.tick_params(axis='both', length=0, pad=9)
ax.set_xlabel('Residentes nacidos fuera de Europa* (% de la población)', labelpad=15, fontsize=12)
ax.set_ylabel('Votos a S + V (% de votos válidos)', labelpad=15, fontsize=12)
fig.text(0.09, 0.946, 'SUECIA  /  ELECCIONES 2026', color='#7c5269', size=10, weight='bold')
fig.text(0.09, 0.896, 'S + V y población nacida fuera de Europa*', size=22, weight='bold')
fig.text(0.09, 0.853, 'S: Socialdemócratas · V: Partido de la Izquierda', size=11, color='#53677c')
fig.text(0.09, 0.818, 'Cada punto es un distrito · votos provisionales de 2026 · población estimada de 2025', size=11, color='#53677c')
n_label = f'{len(points):,}'.replace(',', '.')
r_label = f'{r:.3f}'.replace('.', ',')
ax.text(0.026, 0.955, f'{n_label} distritos\nCorrelación positiva fuerte\nPearson r = {r_label}', transform=ax.transAxes,
        va='top', fontsize=13, linespacing=1.6, weight='bold', color='#22344b',
        bbox={'boxstyle': 'round,pad=0.75', 'facecolor': 'white', 'edgecolor': '#dfe6ef', 'alpha': 0.96}, zorder=5)
fig.text(0.09, 0.137, '* África, Asia, América y Oceanía, más lugar de nacimiento desconocido.', size=9.5, color='#334c65')
fig.text(0.09, 0.112, 'SCB incluye Rusia y Turquía en Europa. Es lugar de nacimiento, no nacionalidad.', size=9.5, color='#334c65')
fig.text(0.09, 0.078, 'Fuentes: Valmyndigheten y SCB · votos: 14/09/2026, 18:30 · población: 31/12/2025.', size=8.5, color='#53677c')
fig.text(0.09, 0.055, 'Cada distrito pesa igual. Esta relación no indica cómo votaron las personas según su origen.', size=8.5, color='#53677c')
fig.text(0.966, 0.020, 'Creado por @Calcetinletal', ha='right', size=10.5, weight='bold', color='#7c5269')
fig.savefig(OUT / (STEM + '.png'), dpi=200, facecolor='white')
fig.savefig(OUT / (STEM + '.svg'), facecolor='white', metadata={'Date': None, 'Creator': 'Creado por @Calcetinletal', 'Description': json.dumps(summary, ensure_ascii=False)})
plt.close(fig)
requirements = ['matplotlib', 'numpy', 'contourpy', 'cycler', 'fonttools', 'kiwisolver', 'pillow', 'packaging', 'pyparsing', 'python-dateutil', 'six']
(OUT / 'requirements.txt').write_text(''.join(f'{name}=={importlib.metadata.version(name)}\n' for name in requirements), encoding='utf-8')
readme = f'''# S+V y resto del mundo por distrito, 2026

Gráfico independiente de la aplicación web. PNG a 200 ppp y SVG vectorial. Firma: Creado por @Calcetinletal.

La etiqueta «nacidos fuera de Europa*» explica la categoría original «resto del mundo + desconocido» y conserva los mismos datos. La nota aclara que SCB incluye Rusia y Turquía en Europa. Lugar de nacimiento no equivale a nacionalidad extranjera.

- {len(points)} de {len(source_rows)} distritos con ambos datos; {sum(excluded.values())} excluidos.
- X: residentes estimados de «resto del mundo + desconocido» / población de la misma tabla SCB.
- Y: votos S + votos V / todos los votos válidos. Se calcula desde recuentos, sin promediar partidos.
- Pearson r: {r:.6f}; Spearman rho: {rho:.6f}. Cada distrito pesa igual.
- Población de 2025 sobre límites 2026. Votos de la instantánea provisional almacenada del 14/09/2026.
- Se incluyen todos los distritos con ambos datos, también los de cobertura parcial; el CSV conserva el diagnóstico.
- La categoría de SCB incluye nacimiento desconocido. En esta clasificación Rusia y Turquía están en Europa.
- Es una asociación territorial, no una estimación del voto individual según origen. No prueba causalidad.

El CSV contiene exactamente los puntos del gráfico. `statistics.json` conserva cálculos, exclusiones, fuentes y SHA-256 del archivo original.

## Reproducir desde la raíz del proyecto

```sh
.venv/bin/pip install -r reports/sv-resto-mundo-2026/requirements.txt
.venv/bin/python scripts/plot_sv_rest_world_2026.py
```

Fuente local: `{SOURCE.relative_to(ROOT)}`. El constructor valida identificadores, años, denominadores, porcentajes y unicidad antes de dibujar.
'''
(OUT / 'README.md').write_text(readme, encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
print(f'Artifacts: {OUT}')
