# 2026 provisional + demografía 2025

Edición activada en el atlas. Instantánea descargada el 16/09/2026 a las 15:16:40 de Estocolmo; fuente actualizada el 16/09/2026 a las 15:15:01. Los 6.312 distritos territoriales están contabilizados. De las 314 unidades de recogida, 175 han informado y 139 están pendientes. Total: 6.487 / 6.626 unidades. Las unidades de recogida se incluyen en la evolución municipal y nacional, pero permanecen fuera del mapa.

```sh
.venv/bin/python scripts/build_2026.py --snapshot 2026-09-16_refresh_02
npm run build
```

Requiere el conjunto definitivo 2022 procesado, dependencias Python, Node/mapshaper y OpenSSL. Usa la caché inmutable. Para refrescar resultados, nueva etiqueta `--snapshot` (fecha/hora); para reproducir exactamente, conservar la caché. `--reuse-crosswalk` reutiliza exclusivamente el overlay existente con los mismos archivos geográficos.

Resultados oficiales: https://resultat.val.se/resultatfiler/val2026/p/rd/Val_2026_preliminar_00_RD.zip . Índice MD5, tres firmas RSA/SHA-256 y SHA-256 local verificados. La ejecución rechaza datos de simulación.

Población, origen, nacimiento y ciudadanía: SCB 31/12/2025 sobre DeSO 2025. Cuadrícula 1 km 2025. Estadística protegida con CKM, interpolación poblacional; no son observaciones exactas del distrito ni medidas de inmigración ocurrida en 2026. Empleo y educación ausentes y desactivados.

Comparabilidad: 5.024 correspondencias uno a uno, 35 con dos distritos previos, 1.253 sin comparación. XLSX y JSON deben coincidir. La etiqueta XLSX «Kan jämföras mot flera» equivale a «Jämförs mot summerat» en JSON. Se suman recuentos antes de obtener porcentajes. 5.059 distritos contabilizados tienen diferencias disponibles; los ausentes no se convierten en cero. No se equipara código idéntico a límite estable.

Salida: `public/data/2026/{districts.json.gz,districts.geojson.gz,joined_2026.csv,provenance.json,quality_report.md}`. Los datos se sirven estáticamente. La fecha y el estado provisional están presentes en interfaz y CSV. No hay actualización automática en tiempo real.

El importador genérico `scripts/import_2026.py` sigue reservado para una futura edición definitiva normalizada. Exige metadatos `status: definitive` y correspondencias uno a uno; el adaptador al formato definitivo deberá auditarse antes de usarlo. No basta con renombrar el provisional.
