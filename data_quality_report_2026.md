# Validación de la edición provisional 2026

Descarga UTC: 2026-09-16T13:16:40.171525+00:00. Fuente actualizada: 2026-09-16T15:15:01 (Europe/Stockholm).
Distritos territoriales: 6312. Contabilizados: 6312. Pendientes: 0. Unidades de recogida excluidas del mapa: 314.
Unidades de recogida contabilizadas: 175 / 314. Total de unidades contabilizadas: 6487 / 6626. Los votos de recogida se incluyen en la evolución municipal y nacional, no se reparten entre distritos territoriales.

## Comprobaciones realizadas

- Firmas RSA/SHA-256 de los tres JSON verificadas con el certificado oficial; MD5 del ZIP contrastado con el índice. SHA-256 y petición de cada original conservados.
- Elección real Val_2026 / RD / preliminär; rechaza simulaciones test=true. Fecha electoral y estado preservados.
- Uniones completas uno a uno, sin códigos duplicados. Porcentajes, suma de partidos, recuentos enteros y participación validados en todos los distritos contabilizados; contraste con porcentajes publicados a su precisión de 0,1 pp.
- Los distritos pendientes conservan null en votos y porcentajes. Todos los distritos conservan su geometría y demografía. Las estadísticas excluyen valores ausentes.
- Correspondencias Excel y JSON coinciden después de traducir Kan jämföras mot flera a Jämförs mot summerat. Dos distritos: suma de numeradores y denominadores, nunca media simple de porcentajes.

## Demografía y límites

SCB 31/12/2025, DeSO 2025, cuadrícula de población 1 km 2025. Interpolación espacial por masa poblacional. CKM añade perturbaciones estadísticas; las sumas de celdas pueden diferir de los totales. Cobertura alta no garantiza precisión local. Empleo y educación quedan sin dato en esta edición.
Se repararon seis geometrías analíticas. En las colecciones se conservaron componentes poligonales; los segmentos sin área se excluyeron. Mapshaper avisó de seis intersecciones no reparadas en su fase de simplificación; se validaron y repararon los polígonos finales. Esto no certifica ausencia total de pequeños solapes entre polígonos.

## Procedencia y diagnósticos

```json
{
  "election_year": 2026,
  "status": "provisional",
  "snapshot": "2026-09-16_refresh_02",
  "downloaded_at": "2026-09-16T13:16:40.171525+00:00",
  "source_updated_at": "2026-09-16T15:15:01",
  "source_timezone": "Europe/Stockholm",
  "district_count": 6312,
  "reported_district_count": 6312,
  "pending_district_count": 0,
  "non_geographic_count": 314,
  "demography_year": 2025,
  "demography_reference_date": "2025-12-31",
  "demography_geometry_year": 2025,
  "grid_year": 2025,
  "election_source_url": "https://resultat.val.se/resultatfiler/val2026/p/rd/Val_2026_preliminar_00_RD.zip",
  "geometry_source_url": "https://www.val.se/download/18.332cf48819bd61ac1513889/1785491689960/valdistrikt-riket-2026.zip",
  "comparability_source_url": "https://www.val.se/download/18.1a2972da19f159e73fd3a47/1787064655347/valdistrikt-jamforelser-mellan-2022-och-2026.xlsx",
  "demography_source_url": "https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__BE__BE0101__BE0101Y/FolkmDesoBakgrKon/",
  "license": "Valmyndigheten: free reuse with attribution; SCB: CC0",
  "signatures_verified": true,
  "election_sha256": "185e534df82aad3ebfad0e9b51c2fa66e5f731b5a5daa595e5513a255a1d8f1b",
  "boundary_repairs": 6,
  "intersections": 37104,
  "source_weight_min": 0.9993174684054226,
  "source_weight_max": 1.0006537554964248,
  "areal_fallback_intersections": 0,
  "coverage_counts": {
    "high_coverage": 6312
  },
  "comparison_counts": {
    "comparable": 5024,
    "not_comparable": 1253,
    "comparable_aggregate": 35
  },
  "comparable_reported_count": 5059,
  "scb_disclosure_control": "CKM: independently protected cells; sums may differ from published totals",
  "education_and_employment": "Not included in this 2025 demographic edition",
  "reporting_unit_count": 6626,
  "reported_unit_count": 6487,
  "reported_non_geographic_count": 175,
  "pending_non_geographic_count": 139
}
```

## Geometría web

```json
{
  "post_rounding_repairs": 1,
  "tolerance_m": 15,
  "method": "mapshaper weighted shared arcs, keep-shapes",
  "bytes_uncompressed": 15406527,
  "bytes_gzip": 4072210,
  "invalid_geometries": 0,
  "p99_relative_area_change": 0.007998391000985018,
  "maximum_relative_area_change": 0.017621509377873233,
  "districts_area_change_above_1pct": {
    "10820104": 0.010132917105067838,
    "18800229": 0.01099513898941739,
    "18800104": 0.011824402185166649,
    "12812407": 0.014256025442543329,
    "12800625": 0.015164416567089415,
    "12800324": 0.013307723422261417,
    "12800107": 0.012268397183375449,
    "12800124": 0.015040468065012452,
    "01260305": 0.010518821300827602,
    "01840223": 0.014181965804957382,
    "01840241": 0.015755453328612706,
    "01804011": 0.010724322327631992,
    "01802523": 0.010540867679757898,
    "01803404": 0.011726742083968143,
    "01801311": 0.010772544468304245,
    "01802728": 0.010768450840865891,
    "01801413": 0.01572872648182451,
    "01802733": 0.010619824426283876,
    "01800917": 0.017621509377873233,
    "01801505": 0.010543890603042548,
    "01802530": 0.010028422194443167,
    "01801417": 0.013961706338922752,
    "01830129": 0.010550087443700923,
    "01380133": 0.011757493782590374,
    "14800417": 0.010292876625228793,
    "14800607": 0.010120266997360116,
    "14800407": 0.010240680513472222,
    "14800312": 0.011305713442999271,
    "14800529": 0.010493209704963806,
    "14800506": 0.01111751857872019,
    "14800508": 0.01738318712514923,
    "14800444": 0.015143144052078332,
    "14800445": 0.013568264857197502,
    "14800513": 0.015604454822312158
  }
}
```

Errores bloqueantes de validación: 0.
