# S+V y resto del mundo por distrito, 2026

Gráfico independiente de la aplicación web. PNG a 200 ppp y SVG vectorial. Firma: Creado por @Calcetinletal.

La etiqueta «nacidos fuera de Europa*» explica la categoría original «resto del mundo + desconocido» y conserva los mismos datos. La nota aclara que SCB incluye Rusia y Turquía en Europa. Lugar de nacimiento no equivale a nacionalidad extranjera.

- 6312 de 6312 distritos con ambos datos; 0 excluidos.
- X: residentes estimados de «resto del mundo + desconocido» / población de la misma tabla SCB.
- Y: votos S + votos V / todos los votos válidos. Se calcula desde recuentos, sin promediar partidos.
- Pearson r: 0.792446; Spearman rho: 0.683166. Cada distrito pesa igual.
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

Fuente local: `public/data/2026/joined_2026.csv`. El constructor valida identificadores, años, denominadores, porcentajes y unicidad antes de dibujar.
