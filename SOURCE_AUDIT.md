# Auditoría de fuentes

Fecha: 2026-09-14. Elección: Riksdag 2022. No se incorporan resultados provisionales de 2026.

| Variables | Fuente y URL | Granularidad / año | Formato | Reutilización | Naturaleza final |
|---|---|---|---|---|---|
| district_id, nombres, municipio, län; votos de todos los partidos, electores, votos válidos, participación | [Valmyndigheten, archivos definitivos](https://www.val.se/valresultat-och-statistik/statistik-och-data/radata-fran-val-2002-2022) | Valdistrikt 2022; también filas agregadas y uppsamlingsdistrikt, que se separan | XLSX | Uso y redistribución libres con atribución a Valmyndigheten | Observado; porcentajes recalculados de recuentos |
| Geometría y códigos | Misma página, 21 ZIP por län | Valdistrikt 2022 | JSON en ZIP, EPSG:3006 | Mismas condiciones | Límite oficial; simplificado únicamente para web |
| population, foreign_background_count/pct | [SCB FolkmDesoBakgrKon](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__BE__BE0101__BE0101Y/FolkmDesoBakgrKon/) | DeSO 2018, población 31-12-2022 | PxWeb JSON-stat2 | SCB CC0 | Observado en DeSO; estimado en valdistrikt |
| foreign_born_count/pct | [SCB FolkmDesoLandKon](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__BE__BE0101__BE0101Y/FolkmDesoLandKon/) | DeSO 2018, 2022 | PxWeb | SCB CC0 | Estimado en valdistrikt |
| foreign_citizens_count/pct | [SCB FolkmDesoMedKon](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__BE__BE0101__BE0101Y/FolkmDesoMedKon/) | DeSO 2018, 2022 | PxWeb | SCB CC0 | Estimado en valdistrikt |
| higher_education_pct | [SCB UtbSUNBefDesoRegso](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__UF__UF0506__UF0506D/UtbSUNBefDesoRegso/) | DeSO 2018, 2022, población 25–64 | PxWeb | SCB CC0 | Estimado; postsecundaria = categorías 5 + 6 / total de 25–64 |
| employment_pct | [SCB BefDeSoSyssN](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__AM__AM0207__AM0207I/BefDeSoSyssN/) | DeSO 2018, población 20–64 según ContentsCode, 2021 | PxWeb | SCB CC0 | Estimado con empleo 2021 etiquetado separadamente |
| median_income | SVT publica un encargo SCB (renta 2020, población 20+) | Valdistrikt 2022 | Embebido en JS | No se ha localizado permiso explícito para ese bulk | Ausente; nunca calcular una mediana de medias/medianas |
| Geometría DeSO | [SCB geodata](https://www.scb.se/vara-tjanster/oppna-data/oppna-geodata/demografiska-statistikomraden-deso/) | DeSO 2018 para 2022; DeSO 2025 para futuro 2026 | WFS / GeoPackage | CC0 | Soporte de interpolación |
| Pesos de población | [SCB cuadrícula](https://www.scb.se/vara-tjanster/oppna-data/oppna-geodata/statistik-pa-rutor/) | Cuadrícula 1 km, 2022 | WFS / GeoPackage | CC0 | Ponderador; distribución uniforme dentro de cada celda |
| Edad / densidad | No incluidas como observaciones directas en el dataset inicial | — | — | — | Ausentes; no sustituidas por conceptos diferentes |
| Ganador, bloques, rankings, asociaciones | Derivados del dataset anterior | Valdistrikt | CSV / JSON | Heredan condiciones | Cálculos descriptivos |

## Inspección de SVT antes de DeSO

Se descargaron y examinaron HTML y scripts, sin scraping masivo:
- https://valresultat.svt.se/2022/ y su `assets/main-d5dc73c5371259c7bab0.js`: el cliente pide ficheros `json/<código>-<tipo>.json` para cartografía.
- https://www.svt.se/datajournalistik/val2022/sa-rostade-svenskarna/ y `BOB-efterval22-app_scatter-bundle-14.js`: contiene un objeto de tabla con `columns`, `index` y `data` (payload embebido, no necesita API por distrito).
- El artículo documenta población/origen 2021-12-31, empleo y renta 2020, educación 2022-01-01. No llamar a todo ello demografía 2022.
- No se encontró una licencia explícita de redistribución de ese payload. Los originales de auditoría quedan en caché local excluida de git; no se publican.
- Se inspeccionó la alternativa SCB directa: https://experience.arcgis.com/experience/6284f55fe08444a9bca99a8590864d15 → dashboard `42c30d8e38f5416a931805ad8b260130` → webmap `35290adb8a9643399990f2275ac886e9` → FeatureServer `https://services8.arcgis.com/9CUL84k8apjo6IDh/arcgis/rest/services/Valdistrikt_SocEk_ValResult_2022/FeatureServer/0`. Tiene origen de **electores**, no `utländsk bakgrund` de todos los residentes. No se confunden los denominadores.

## Decisión de unión

Caso B autorizado: intersecciones DeSO 2018 ∩ valdistrikt 2022, en EPSG:3006, con densidad de la cuadrícula SCB 2022. Normalizar las masas por DeSO y transferir recuentos; dividir numerador y denominador transferidos, nunca promediar porcentajes sin sus bases. Si no existe masa de cuadrícula para un DeSO, usar área únicamente para ese DeSO y etiquetar el distrito afectado. No usar centroides. Publicar cobertura geométrica separada de completitud estadística y peso dominante. Los controles de calidad no son intervalos de confianza.

Mantener resultados de recogida sin geometría en una tabla separada. No prorratearlos sobre los distritos. La suma de votos cartografiados no equivale al total oficial nacional.

## Secuencia y estructura

1. Este documento, configuración de fuentes y comprobación de metadatos.
2. Descargas inmutables con SHA-256 y fecha, normalización, overlay, `joined_2022.csv`, informe de calidad y muestra de diez distritos.
3. Vite + TypeScript + MapLibre, mapas electoral/demográfico, ficha, filtros y URL.
4. Comparador sincronizado, bivariado, scatter, correlaciones, regresión descriptiva, bins, deciles, rankings y CSV.
5. Simplificación offline, datos comprimidos, accesibilidad, adaptación móvil y GitHub Pages.
6. Importador 2026 que exige datos definitivos y clasificación explícita de comparabilidad.

Rutas previstas: `src/{components,maps,charts,analysis,utils}`, `scripts/`, `config/`, `data/{raw,processed,elections/2022,elections/2026}`, `public/data`, `methodology/`, `.github/workflows/deploy.yml`.

## Cierre de auditoría tras descarga

Geografía verificada: 5.984 DeSO, versión `2018_v3`, y 6.264 valdistrikt con geometría. El XLSX incluye además 314 unidades de recogida. SCB empleo llega a 2021: ContentsCode indica población 20–64 aunque el título histórico menciona 16–64. Se usa el universo del contenido y se etiqueta 2021. No hay ausentes en las tablas seleccionadas. El complemento de nacidos en Suecia incluye país desconocido; el complemento de ciudadanía sueca incluye apátridas/desconocida, conforme a las categorías agrupadas de SCB. No confundir estos indicadores con datos individuales de nacionalidad o lugar de nacimiento conocidos.


## Ampliación real 2026 (14 de septiembre)

Se descargaron los resultados preliminares oficiales, no simulaciones, del ZIP `https://resultat.val.se/resultatfiler/val2026/p/rd/Val_2026_preliminar_00_RD.zip`. Se verificaron índice MD5 y las tres firmas RSA/SHA-256 con el certificado oficial. El JSON contiene 6.312 distritos territoriales (6.276 reportados / 36 pendientes) y 314 unidades de recogida. Los nulos de distritos pendientes se conservan.

La geometría nacional 2026 se descargó del catálogo oficial. Se auditaron columnas, CRS SWEREF99 TM, reparaciones y anti-joins. La correspondencia XLSX de agosto coincide con las listas JSON: 5.024 uno a uno y 35 casos de dos distritos, con una traducción explícita de etiquetas («Kan jämföras mot flera» / «Jämförs mot summerat»). Otros 1.253 quedan sin diferencia. Se comparan recuentos provisionales 2026 con definitivos 2022, sin equiparar fase de recuento.

SCB: las tres tablas de población/origen/nacimiento/ciudadanía ya incluyen 2025. Se consultan exactamente los 6.160 códigos `_DeSO2025`, ambos sexos, Tid=2025, junto a DeSO_2025 y befolkning_1km_2025. Origen extranjero usa la categoría publicada; nacimiento y ciudadanía usan complementos del total con las mismas notas de desconocidos. La nota oficial incorpora CKM desde 2025: perturbaciones controladas por confidencialidad, sumas no necesariamente aditivas. No se sustituyen controles socioeconómicos por cifras antiguas. Las fuentes 2026 están fijadas en `scripts/build_2026.py`.

El cruce usa 37.104 intersecciones reales; no necesitó reparto areal. Se conserva 2022. La nueva edición no se denomina «demografía 2026»: su fecha es 31/12/2025. Ver `data_quality_report_2026.md` y `public/data/2026/provenance.json`.


## Países de nacimiento · SCB 2025

La tabla DeSO FolkmDesoLandKon solo publica Suecia, Europa fuera de Suecia y resto del mundo con desconocidos; no contiene países individuales. Se revisó el catálogo oficial DeSO y la tabla detallada `BE/BE0101/BE0101E/FolkmRegFlandKCKM`, publicada 24/02/2026, referencia 31/12/2025. Esta última tiene 312 ámbitos (país, 21 län y 290 municipios), 189 opciones de nacimiento incluido el total, y tres opciones de sexo. Se descargaron todos los ámbitos y países, ambos sexos (`TotSa`), 2025.

Fuente: https://www.statistikdatabasen.scb.se/pxweb/en/ssd/START__BE__BE0101__BE0101E/FolkmRegFlandKCKM/ . Petición y SHA-256 conservados bajo `data/raw/scb/countries/`. Hay 58.656 celdas país/ámbito sin contar el total; 39.730 no tienen recuento individual publicado. No se convierten esos ausentes en cero. La nota de SCB establece agrupación bajo 10 personas regionalmente / 20 nacionalmente, además de protección CKM. Las celdas ausentes se muestran como agrupadas/sin dato; ceros individuales ambiguos también se preservan sin inferir un porcentaje cero exacto.

Se construyó una vista municipal independiente, no una estimación por valdistrikt. Cada porcentaje divide recuento del país entre la población total publicada del mismo ámbito. Los recuentos nacionales y por län se leen directamente. Se incluyeron categorías agrupadas y países históricos con etiquetas distintas. Los contornos son polígonos electorales 2026 disueltos por municipio, simplificados conjuntamente a 50 metros y validados en WGS84; su finalidad es visual. Los 290 códigos coinciden exactamente entre geometría y tabla. Ver `public/data/countries/provenance.json` y `scripts/build_countries.py`.

## Agrupaciones geográficas y disponibilidad de religión

Se auditó la clasificación [ONU M49](https://unstats.un.org/unsd/methodology/m49/overview/), conservada con fecha de descarga y SHA-256 en `data/raw/scb/countries/un_m49_overview.html`. La transformación `scripts/build_birth_regions.py` asigna las 188 categorías a continentes o sin asignación; valida una partición exhaustiva sin duplicados y produce diez agrupaciones, algunas solapadas. Se conservan códigos históricos: YU/CS en Europa meridional, QT en Europa oriental; XK en Europa meridional y TW en Asia oriental. SU (antigua URSS) queda sin asignar por ser transcontinental. ÖOF y OVFOD no se distribuyen por continente. Turquía y Chipre son Asia; Rusia, Europa. Esta convención no equivale necesariamente a las agrupaciones de nacimiento propias de SCB.

Cada cifra regional suma únicamente celdas de países publicadas para el mismo ámbito (municipio, län o país). Se guardan la lista de miembros y las celdas ausentes. Si no existe ninguna celda utilizable, el resultado es nulo. No se presentan los subtotales como totales completos ni como límites inferiores exactos, dado el control CKM. Se publican 3.120 observaciones para diez grupos y 312 ámbitos con denominador poblacional local. Los países agrupados impiden garantizar completitud incluso cuando no faltan celdas individuales de la lista.

Religión: se revisaron las [estadísticas de subvenciones SST](https://www.myndighetensst.se/bidrag/bidragsstatistik). Miden miembros y participantes regulares registrados de determinadas comunidades; no son un recuento municipal comparable de todos los musulmanes, cristianos o hindúes residentes. La tabla SCB usada no incluye religión. Se documenta esta limitación en la interfaz y la procedencia; no se imputan religiones según lugar de nacimiento ni se equipara India con hinduismo.

## DeSO → distrito electoral: tres regiones de nacimiento

Se descargaron sv/eu/öv/tot de FolkmDesoLandKon para 2022 (5.984 DeSO 2018) y 2025 (6.160 DeSO 2025), ambos sexos. Se conservaron solicitudes y SHA-256 en `scb/birth_regions_deso_2022.json` y `scb/birth_regions_deso_2025.json`. Las definiciones oficiales son Suecia; Europa excepto Suecia, incluyendo Rusia y Turquía; y resto del mundo incluyendo dato desconocido. No equivalen a las agrupaciones ONU M49 de la vista municipal. La fuente no permite separar África, Asia ni países individuales en DeSO.

La transformación `scripts/build_district_birth_regions.py` aplica los pesos de intersección poblacional existentes a los tres recuentos y al total de la misma tabla. Calcula porcentajes después de agregar recuentos y registra método, completitud, fecha, fuente y discrepancia entre suma de componentes y total. Si falta una celda contribuyente, no publica una suma parcial como estimación completa. No renormaliza pesos ni componentes. Hay datos fuente completos para los 6.264 / 6.312 distritos, manteniendo los diagnósticos existentes de cobertura espacial (completitud de celdas no implica cobertura geométrica perfecta ni exactitud demográfica).

Las celdas publicadas están protegidas estadísticamente: CTA en la edición anterior y CKM desde 2025. Pueden no sumar el total. Se usan como observaciones de origen protegidas y se etiqueta la salida como estimación espacial. Los residentes y los electores son universos distintos. El cruce no identifica la composición religiosa ni el voto de personas individuales. Los resultados electorales mantienen sus recuentos y estados originales.

## Revisión adicional de organismos oficiales (14/09/2026)

La inexistencia de datos oficiales distritales no es una conclusión válida. Se volvió a consultar el servicio directo SCB y se descargaron los 6.264 registros de 2022: todos coinciden por código con el atlas y tienen recuentos Fo_Utrikes / FO_TOTföd completos. Son indicadores sobre electores con denominador propio, no todos los residentes. SCB ofrece además tablas a medida por valdistrikt, incluyendo país de nacimiento y origen extranjero. Ver OFFICIAL_DISTRICT_AUDIT.md para enlaces, consultas y verificaciones. La fuente DeSO sigue sustentando las estimaciones actuales de residentes; la disponibilidad detallada por continente y distrito debe distinguir datos abiertos existentes de extracciones por encargo.


## Actualización 2026-09-15_000643

Resultados preliminares descargados el 15/09/2026 a las 00:06:43 de Estocolmo, con fuente actualizada a las 18:30:03 del 14/09/2026. Se verificaron índice MD5 y las tres firmas RSA/SHA-256. 6.312 de 6.312 distritos territoriales informados; 0 pendientes. Los 36 pendientes anteriores ya tienen votos; no cambian los resultados de los 6.276 previamente informados. Quedan 16 empates de partido y ningún ganador sin determinar. Los límites y la comparabilidad XLSX coinciden por SHA-256 con los archivos anteriores, permitiendo reutilizar el cruce espacial. Las 5.059 comparaciones válidas tienen resultados.

También se inspeccionó y verificó el ZIP del escrutinio definitivo (slutlig), actualizado a las 19:32:03: solo 15 de 6.626 unidades de recuento estaban contabilizadas. La página conserva el provisional completo y su etiqueta de provisionalidad. El JSON completo de diferencias está en data/2026/refresh_summary.json. SHA-256 del ZIP provisional: `e30649614e124867a481a16c6218446c1a8c89179df373e544e4051a315b134c`.


## Actualización: renta neta distrital (15/09/2026)

Se verificó la tabla oficial SCB Tab1InkDesoRegso (actualizada 20/01/2026):
https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__HE__HE0110__HE0110I/Tab1InkDesoRegso/

`mean_net_income` utiliza media (`0000089T`) y personas (`0000089O`), tipo neto
`NeInk`, ambos sexos. Población 20+ de año completo según SCB; ambas series en
precios constantes de 2024. El mapa 2022 usa renta 2022 y el 2026 renta 2024.
Se estiman sumas y denominadores sobre los polígonos electorales con los cruces
poblacionales existentes; no es renta distrital observada ni se aproxima la mediana
mediante medias de medianas. La ausencia de `median_income` sigue siendo intencionada.

Los cuatro originales de esta incorporación (metadatos, definición HTML, JSON-stat
2022 y 2024) están fijados en caché y registrados en SOURCES.md con SHA-256.
La media queda disponible en 6.259/6.264 distritos de 2022 y 6.312/6.312 de 2026.
Los cinco sin dato no se imputan. Ver income_provenance.json por edición para
universo, fórmula, años geográficos, cobertura y limitaciones. No describe únicamente
a los electores ni permite atribuir votos individuales a grupos de renta.

## Actualización electoral del 16 de septiembre de 2026

- Instantánea `2026-09-16_refresh_02`: fuente preliminar de Valmyndigheten actualizada 2026-09-16T15:15:01 (Europe/Stockholm), descargada 2026-09-16T13:16:40.171525+00:00 UTC. SHA-256 `185e534df82aad3ebfad0e9b51c2fa66e5f731b5a5daa595e5513a255a1d8f1b`. Índice MD5 y las tres firmas RSA/SHA-256 coinciden y se verificaron.
- 6.312 distritos territoriales contabilizados; 175/314 unidades de recogida. La cifra oficial de 6.487/6.626 incluye ambos tipos: no debe compararse solo con las 6.312 filas territoriales del mapa.
- Se consultó también el archivo `slutlig`, actualizado 2026-09-16T15:15:13: 1.331 distritos contabilizados, todavía parcial. Se conserva una edición provisional completa y no se mezclan recuentos.
- Los votos por partido de los 6.312 distritos territoriales no cambiaron respecto a la instantánea anterior. Cambiaron electores y participación en 96 distritos (hasta dos electores; hasta 0,149195 puntos de participación); se regeneraron diferencias disponibles. Las series municipales y nacionales incorporan las unidades de recogida nuevas.
- Límites y correspondencias nuevos tienen hashes idénticos a los originales anteriores: se reutilizó el cruce poblacional. Todas las variables demográficas y de renta se verificaron idénticas tras regenerar el dataset.
- La primera descarga `2026-09-16_refresh` no coincidió con su índice durante la actualización remota y se descartó. Permanece en el inventario como descarga auditada, pero no se usa para publicar resultados. La segunda instantánea supera todas las comprobaciones.


## Historia socioeconómica y edades — 16 septiembre 2026

Fuentes SCB consultadas: Tab1InkDesoRegso (renta), UtbSUNBefDesoRegso y
UtbSUNBefDesoRegsoN (educación), ArRegDesoStatusN (BAS), FolkmDesoAldKon (edad).
Metadatos, consultas, respuestas, fechas y SHA-256 se conservan en caché inmutable.
La renta está en precios del último año publicado (2024); nunca se promedian medianas.
Educación contiene todas las cinco categorías en el denominador, incluida desconocida,
y ambas categorías postsecundarias en el numerador. Desde 2023 el universo es 25–65,
frente a 25–64 hasta 2022. Aunque la fuente es SCB, esta tabla detallada figura con
Officiell statistik: Nej. No se presenta como observación electoral oficial.
BAS se consulta en 20–64 para todos sus años (2020–2024): empleo / población,
desempleo / población activa; no se une a la serie RAMS.
La población y las edades se refieren a 31/12; CKM comienza en 2025.

Se reutilizan los cruces históricos de nacimiento, con cuadrículas contemporáneas
desde 2015. Para 2010–2014 solo se admiten uniones casi completas de DeSO.
Se excluyen contribuyentes ausentes y fuentes con cobertura insuficiente, sin
renormalizar pesos ni completar con el municipio. Numeradores y denominadores
se agregan antes de dividir; población total se agrega como recuento.
La historia muestra la geografía de cada edición y los enlaces no verificados.
El agregado BAS de municipio/län/país es suma de DeSO; para las demás variables
se publica el agregado SCB, sin mezclarlo con el distrito.

Los nuevos mapas conservan los archivos originales de voto, origen y renta.
Un suplemento separado aporta educación, empleo, desempleo y edades. En la edición
2026 usa el cruce/retícula 2025: educación/edad 2025 y BAS 2024. No es un crecimiento
de 2024 a 2026. La edición 2022 conserva 95 casos sin estimación por cobertura
espacial insuficiente, en vez de imputarlos. Cobertura por variable/año y huellas de
los cruces en history/socio/provenance.json.

Validación: 522.707 observaciones revisadas (orden/duplicados/años/rangos); 195
estimaciones recalculadas independientemente con celdas y pesos de origen. Los
agregados publicados de muestras municipales y nacionales coinciden con SCB.
Ninguna columna preexistente de los distritos es reemplazada por el suplemento.
