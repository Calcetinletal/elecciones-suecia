# Revisión de fuentes oficiales por distrito electoral

Fecha de consulta: 14/09/2026.

La ausencia de una tabla abierta de todos los residentes por continente/país en la fuente integrada no demuestra ausencia de estadística oficial distrital. SCB publica indicadores directos sobre electores y ofrece tablas a medida por valdistrikt. La elección DeSO del atlas es una decisión de fuente/universo, no una imposibilidad general.

## Descarga directa SCB, Riksdag 2022

- Catálogo oficial: https://www.scb.se/hitta-statistik/regional-statistik-och-kartor/kartor/
- Aplicación enlazada por SCB: https://experience.arcgis.com/experience/6284f55fe08444a9bca99a8590864d15
- Servicio inspeccionado: https://services8.arcgis.com/9CUL84k8apjo6IDh/arcgis/rest/services/Valdistrikt_SocEk_ValResult_2022/FeatureServer/0
- Campos relevantes: Valdistrik (código), Fo_Utrikes (nacidos fuera), FO_TOTföd (denominador propio del indicador), Röstberättigade (electores del resultado). Otros campos de edad, educación e ingresos.
- Descargados 6.264 registros, 6.264 códigos únicos: coincidencia exacta con los códigos del atlas 2022. Ningún nulo en los dos campos de nacimiento; ningún numerador negativo o superior al denominador.
- En 6.260 registros el denominador de nacimiento difiere del total electoral de electores: no sustituir FO_TOTföd por Röstberättigade ni por la población total.
- Ejemplo 01250905: Fo_Utrikes=140; FO_TOTföd=1269; Röstberättigade=1295.
- La descripción de la aplicación caracteriza electores. No es la composición de todos los residentes ni el origen extranjero de los padres. No contiene columnas por África, Asia, países individuales o religión.
- La descarga fue tabular, sin geometrías. Verificar correspondencia geométrica/metodología y condiciones completas antes de integrar como indicador separado. Los códigos coinciden; esto no convierte todos los demás universos o geografías en equivalentes.
- Originales, consultas y SHA-256: data/raw/audit/district_official_review_20260914_*.json. Comprobaciones: data/raw/audit/district_official_review_checks.json.

## Otras publicaciones directas

SCB documenta también un mapa de las europeas 2024 por valdistrikt con edad, educación, nacimiento fuera e ingresos de electores. La página explica exclusiones de ciertos electores en las variables de contexto. No trasladar automáticamente esas exclusiones a 2022 sin documentación específica.

https://www.scb.se/pressmeddelande/analysera-valdeltagandet-i-eu-valet-med-scbs-verktyg/

SCB publicó en marzo de 2026 una herramienta sobre participación de las municipales 2022 por RegSO, con variables de nacimiento y ciudadanía. Es una geografía distinta y no es un recuento de votos por partido para 2026.

https://www.scb.se/pressmeddelande/stora-skillnader-i-valdeltagande--sa-ser-det-ut-i-din-del-av-kommunen/

Valmyndigheten ofrece resultados, cartografía y estadísticas de electores directamente por distrito en 2022/2026. En las fuentes revisadas no se localizó un desglose de residentes por continentes/países para todos los distritos 2026.

https://www.val.se/valresultat-och-statistik/statistik-och-data/radata-val-2026

## Tablas a medida de SCB

SCB enumera explícitamente valdistrikt entre las geografías para pedidos de estadística y país de nacimiento, ciudadanía y origen sueco/extranjero entre las variables poblacionales.

https://www.scb.se/vara-tjanster/bestall-data-och-statistik/bestall-statistiktabeller/amnesomraden/

También permite áreas propias y estadísticas basadas en registros georreferenciados:

https://www.scb.se/vara-tjanster/bestall-data-och-statistik/bestall-statistiktabeller/geografiska-indelningar-och-digitala-granser/

SCB envía un presupuesto después de recibir una consulta, y la consulta no es vinculante. No se ha enviado ninguna solicitud ni encargado trabajo.

https://www.scb.se/vara-tjanster/bestall-data-och-statistik/bestall-statistiktabeller/

Una solicitud para este proyecto debería especificar: todos los residentes a 31/12/2025; límites oficiales valdistrikt 2026; población total y grupos de nacimiento definidos explícitamente, incluidos Suecia, Europa, África, Asia, América, Oceanía y desconocido; recuentos con códigos territoriales y condiciones de confidencialidad/reutilización. La disponibilidad exacta, agrupaciones y precio deben confirmarse con SCB. No deducir religión de nacimiento.

## Implicación para la web

La web conserva sus estimaciones DeSO de residentes. La fuente directa 2022 permitiría un indicador adicional sobre electores con denominador propio, sin reemplazar silenciosamente las variables de residentes. Para continentes/países de todos los residentes por distrito 2026, la vía oficial confirmada es consultar una extracción específica a SCB; no se ha encontrado una descarga nacional abierta equivalente en esta revisión.
