# Suecia · Atlas electoral y demográfico

Atlas interactivo **100 % estático**, en español, para explorar resultados del Riksdag y composición demográfica por **valdistrikt**. Sin backend, claves API, servicios de pago, Mapbox ni mapa base externo.

Incluye datos reales de **6.264 distritos de 2022**. Los 314 distritos de recogida de votos se conservan por separado. La demografía por distrito es una **estimación espacial** desde SCB DeSO 2018 y la cuadrícula oficial de población de 2022. No son observaciones exactas de cada valdistrikt. Educación: 2022; empleo: 2021. Renta mediana, edad y densidad: no disponibles.

La web abre la **edición provisional 2026**, actualizada con la fuente oficial del **16/09/2026 a las 15:15:01 de Estocolmo**. Descarga: 16/09/2026 15:16:40. Los 6.312 distritos territoriales están contabilizados; 0 pendientes. Hay además **175 de 314 unidades de recogida tardía contabilizadas**: se incluyen en las series municipales y nacionales, nunca se reparten entre los polígonos del mapa. En total han informado 6.487 de 6.626 unidades. La demografía sigue siendo del 31/12/2025 y la renta, de 2024. El recuento definitivo está en curso y no se mezcla con esta edición provisional. La web muestra la fecha y es una instantánea estática.

## Abrir localmente

Recomendado: Node.js 22 y npm. Los datos publicados ya están incluidos; **no hace falta ejecutar Python** para usar la web.

```sh
npm install
npm run dev
```

Abrir la URL que imprime Vite, normalmente http://localhost:5173. En este equipo el proyecto está en WSL: `/home/miguelcastresana/cositas/elecciones_suecia`. Ejecutar los comandos en Ubuntu/WSL, donde están Node y npm.

```sh
npm ci             # instalación reproducible con package-lock.json
npm run build      # genera dist/
npm run preview    # sirve dist/ para revisar la compilación
```

El navegador debe admitir WebGL y DecompressionStream (navegadores modernos). Abrir mediante HTTP, no directamente como `file://`. Si WebGL no está disponible, el análisis y la descarga tabular siguen siendo utilizables.

## Qué incluye

- Mapa electoral: ganador, cada partido y participación; ficha completa al pulsar.
- Mapa demográfico: origen extranjero, nacimiento fuera y ciudadanía extranjera, con notas de denominadores y categorías desconocidas de SCB.
- Bivariado 3×3 con terciles nacionales fijos y selector de partido.
- Ganador dentro de intervalos de composición demográfica.
- Dos mapas con centro y zoom sincronizados.
- Búsqueda de municipios/distritos, filtros por län/municipio y cobertura.
- Top/Bottom 10, distribución del indicador y ranking nacional de la ficha.
- `/analysis/`: scatter, Pearson, Spearman con empates, OLS descriptiva, participación por separado, bins, deciles y ponderación de medias.
- Regresión múltiple exploratoria con selección de controles disponibles, casos completos y coeficientes por desviación típica.
- CSV filtrado con fuentes, años, métodos y calidad; enlaces compartibles que conservan controles, distrito y cámara.
- `/methodology/`, formato numérico español/sueco, búsqueda mediante teclado y panel móvil plegable.
- Importador normalizado 2026 y deltas exclusivamente para unidades declaradas comparables.

El aviso sobre correlaciones ecológicas permanece visible. Ningún resultado se interpreta como voto individual, causalidad o explicación política automática.

## Países de nacimiento

La pestaña **Países** (`/countries/`) incorpora la tabla oficial SCB a **31/12/2025**, con 188 categorías de nacimiento, incluidos países históricos, país desconocido y otros países agrupados. El mapa usa los **290 municipios**, con selección de país, län, municipio y tabla completa de cantidades y proporciones. El porcentaje divide cada recuento entre **todos los residentes** del área elegida. Las cifras nacionales y por län proceden de las filas publicadas, no de sumar celdas municipales.

Es una vista municipal independiente: los datos por país no se reparten artificialmente por distrito electoral. Los límites de visualización se obtienen disolviendo los distritos 2026; no alteran las observaciones de SCB. El país de nacimiento no equivale a ciudadanía ni ascendencia. SCB agrupa países con menos de 10 personas regionalmente (20 a nivel nacional); la vista muestra los ausentes como agrupados/sin dato. CKM hace que componentes y totales no coincidan necesariamente. La fecha demográfica sigue siendo 2025 aunque se esté analizando la elección de 2026.

```sh
.venv/bin/python scripts/build_countries.py
npm run build
```

Requiere `data/processed/boundaries_2026.parquet` del pipeline 2026, Python y Node/mapshaper. Cada descarga queda cacheada con petición y SHA-256. Las fuentes se fijan en el script. Archivos: `public/data/countries/`, incluidos CSV completo y procedencia. La web sigue siendo 100 % estática.

## Reproducir los datos

Python 3.12, Node.js 22 y npm. Los paquetes geoespaciales se usan **offline**, durante el ETL.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
npm ci
python make_data.py
```

Windows con Python nativo: activar `.venv\Scripts\Activate.ps1`. En este workspace se ha utilizado Ubuntu 24.04 / WSL con Python 3.12.

Cada script se puede ejecutar por separado desde cualquier directorio; resuelve las rutas desde su propio archivo. Deben existir los productos de los pasos previos:

| Paso | Comando | Producto |
|---|---|---|
| Elección | `python scripts/download_election_2022.py` | XLSX original inmutable |
| Límites | `python scripts/download_boundaries_2022.py` | 21 ZIP originales |
| SCB | `python scripts/download_demography.py` | Tablas PxWeb, DeSO, cuadrícula y demografía normalizada |
| Normalizar | `python scripts/normalize_data.py` | Elección, recogida de votos y límites analíticos |
| Overlay | `python scripts/build_crosswalk.py` | Intersecciones y pesos de población |
| Unir | `python scripts/build_dataset.py` | `joined_2022.csv` y tabla web comprimida |
| Simplificar | `python scripts/simplify_geometries.py` | Geometría web WGS84 comprimida |
| Muestra | `python scripts/verify_sample.py` | Diez comparaciones con páginas SVT |
| Validar | `python scripts/validate_data.py` | Informe de calidad; falla si hay errores bloqueantes |
| Procedencia | `python scripts/build_provenance.py` | SOURCES.md, manifiesto y documentación publicada |

Para reanudar: `python make_data.py --from-step build_dataset.py`. Para experimentar explícitamente con interpolación areal: `python scripts/build_crosswalk.py --areal`; regenerar los pasos posteriores. **Cambia la metodología**, queda etiquetada en el dataset; el conjunto entregado usa ponderación poblacional.

`data/raw/` se cachea y se excluye de git: puede contener mucho volumen y materiales de SVT cuya redistribución no está autorizada. El pipeline verifica SHA-256, URL y petición antes de reutilizar un original. Nunca sobrescribe un raw existente con otra versión. Conservar esa caché para reproducción exacta del snapshot; si una fuente remota cambia en una descarga futura, comparar sus hashes con `public/data/provenance.json` y auditarla.

## Datos y calidad

- [SOURCE_AUDIT.md](SOURCE_AUDIT.md): investigación previa, variables y elección de fuentes.
- [SOURCES.md](SOURCES.md): URLs reales, fecha de descarga, SHA-256 y transformaciones.
- [LICENSE_DATA.md](LICENSE_DATA.md): condiciones de reutilización.
- [MANUAL_CHECKS.md](MANUAL_CHECKS.md): diez distritos de diez municipios contrastados con SVT.
- [data_quality_report.md](data_quality_report.md): validaciones, ausentes, anti-joins, reparaciones, cobertura y simplificación.
- [CSV completo](public/data/2022/joined_2022.csv).

No hay datos sintéticos en la web. Los tests matemáticos usan fixtures sintéticos aislados, exclusivamente para verificar fórmulas.

Hay **77 distritos con cobertura parcial** según los diagnósticos definidos. Una cobertura alta no garantiza exactitud: la cuadrícula es de 1 km y la composición se supone uniforme dentro de cada DeSO. En la muestra, las estimaciones de 2022 difieren de la demografía exacta de 2021 mostrada por SVT; no se equiparan ni se ocultan esas diferencias.

El ETL conserva las geometrías analíticas de alta resolución en GeoParquet EPSG:3006. Solo para visualización se simplifican arcos compartidos a 15 m, con control de geometrías y de variación de área. GeoJSON: ~15,6 MB sin comprimir, ~4 MB gzip. Al quedar por debajo del umbral de 20 MB se sirve GeoJSON comprimido; la tabla se descarga antes y MapLibre se carga por separado. El navegador no hace overlays.

## GitHub Pages

1. Crear un repositorio y subir el código junto con **`public/data/`**, `package-lock.json` y los documentos de fuentes. No subir `.venv`, `node_modules`, `data/raw`, ni `dist`.
2. En **Settings → Pages → Source**, seleccionar **GitHub Actions**.
3. Cada push a `main` ejecuta `.github/workflows/deploy.yml`: `npm ci`, pruebas, build y despliegue de `dist/`.

Vite calcula `/<repositorio>/` a partir de `GITHUB_REPOSITORY`. Los repositorios `<usuario>.github.io` usan `/`. No hace falta editar código al cambiar de nombre. Para un dominio personalizado, configurar `VITE_BASE_PATH=/` durante el build.

Comprobar manualmente un prefijo:

```sh
VITE_BASE_PATH=/mi-repositorio/ npm run build
```

En PowerShell: `$env:VITE_BASE_PATH='/mi-repositorio/'; npm run build`.

`/analysis/` y `/methodology/` tienen archivos HTML físicos en `dist/`, por lo que se pueden recargar o compartir sin un servidor de rutas. `.nojekyll` se genera automáticamente. No hace falta un `404.html` que simule el enrutamiento.

Publicado en https://calcetinletal.github.io/elecciones-suecia/ mediante el workflow de GitHub Pages.

## Configuración y URLs

- `config/parties.json`: nombres y colores de partido. Recompilar tras editar.
- `config/blocks.json`: agrupaciones por año. 2026 no hereda automáticamente las de 2022.
- `config/sources.json`: URLs y tablas auditadas.
- `public/data/manifest.json`: ediciones disponibles; la aplicación activa ediciones definitivas o provisionales identificadas como tales.

Ejemplo:

```text
?year=2022&view=compare&party=SD&municipality=0180&metric=foreign_background_pct&district=01801506&locale=es-ES
```

Otros parámetros: `county`, `band`, `quality`, `weight`, `analysisY`, `size`, `lng`, `lat`, `zoom`. Los códigos se guardan como texto para preservar ceros iniciales. Se acepta también el nombre municipal exacto en la URL y se normaliza al código.

## Reproducir o actualizar 2026

Con la caché incluida en este equipo:

```sh
.venv/bin/python scripts/build_2026.py --snapshot 2026-09-16_refresh_02
npm run build
```

Para descargar una instantánea nueva, usar una etiqueta nueva, por ejemplo `--snapshot 2026-09-15_am`. Reutilizar la etiqueta conserva exactamente el original cacheado. La demografía de 2025 queda fijada en su propia caché. `--reuse-crosswalk` permite omitir el overlay ya calculado si se conservan las mismas geometrías 2026 / 2025 y la misma cuadrícula. OpenSSL debe estar instalado para verificar las firmas oficiales.

El programa descarga el índice, ZIP electoral, geometrías y correspondencias; verifica firmas y hashes; consulta SCB; calcula el overlay, diferencias, controles de calidad y archivos estáticos. No descarga datos de simulación ni activa un archivo como definitivo. Si índice y ZIP cambian entre descargas, aborta y requiere otra etiqueta. Para reproducir exactamente una fecha antigua es necesario conservar su caché: la URL electoral publica una instantánea mutable.

Las diferencias usan los recuentos definitivos locales de 2022 y el provisional 2026, únicamente con acuerdo entre correspondencia oficial y metadatos del recuento. En los 35 casos comparables con dos distritos anteriores se suman numeradores y denominadores. Hay 1.253 distritos sin comparación válida y todos los comparables tienen recuento. Ver [edición 2026](data/elections/2026/README.md), [calidad](data_quality_report_2026.md) y [CSV 2026](public/data/2026/joined_2026.csv).

## Pruebas

```sh
npm test
.venv/bin/pytest -q tests/test_pipeline.py
python scripts/validate_data.py
# Navegación, móvil, mapas y rutas reales con prefijo /atlas/
PLAYWRIGHT_BROWSERS_PATH=.playwright npx playwright install chromium
VITE_BASE_PATH=/atlas/ npm run build
PLAYWRIGHT_BROWSERS_PATH=.playwright npx playwright test
```

Las pruebas de navegador sirven `dist/` con un servidor estático sin fallback SPA y bloquean las peticiones externas en la prueba principal. No modifican los datos publicados.

## Estructura

```text
src/                 Interfaz, mapas, componentes, gráficos y estadística
scripts/             ETL y herramientas reproducibles
tests/               Pruebas matemáticas, geoespaciales y navegador
config/              Partidos, bloques y fuentes
data/raw/            Originales locales inmutables, excluidos de git
data/processed/      Resultados analíticos reproducibles, excluidos de git
data/elections/      Ediciones 2022 y 2026 provisional
public/data/         Únicos datos servidos por la web
methodology/         Referencia a la metodología documentada
.github/workflows/   Despliegue automático de GitHub Pages
```

Código MIT. Datos: condiciones separadas en LICENSE_DATA.md.

## Regiones de nacimiento

En `http://localhost:5173/countries/?country=REG_NON_EUROPE`, elegir «Agrupar por → Regiones geográficas». Se incluyen África, Asia, Europa con/sin Suecia, América, América septentrional, América Latina y Caribe, Oceanía, fuera de Europa y sin asignación continental. Los filtros territoriales, el mapa y el CSV siguen disponibles.

Son subtotales de países publicados para 2025, divididos entre todos los residentes del ámbito, no totales continentales completos. Se muestra cobertura de celdas: las ausencias por confidencialidad no se convierten en cero y los países agrupados no se distribuyen artificialmente. Las categorías se solapan. La clasificación usa ONU M49 con excepciones históricas documentadas; fuera de Europa no equivale a fuera de la UE.

`scripts/build_countries.py` incorpora automáticamente esta transformación. Para regenerar solo las agrupaciones desde el archivo de países existente:

```sh
.venv/bin/python scripts/build_birth_regions.py
```

Definiciones y correspondencias: `public/data/countries/birth_regions_definition.json`. Subtotales y cobertura: `public/data/countries/birth_regions_2025.csv`.

La vista explica la ausencia de datos municipales religiosos comparables en las fuentes consultadas. SCB no registra religión en esta tabla; los miembros/participantes de comunidades religiosas de SST tienen otro universo. No se infiere religión a partir de país o continente de nacimiento.

## Nacimiento y resultados en los mismos distritos

Abrir `http://localhost:5173/?year=2026&view=compare&metric=born_rest_world_unknown_pct&party=SD`. El selector Indicador permite Suecia, Europa excepto Suecia y resto del mundo + país desconocido. La izquierda muestra la estimación demográfica y la derecha el voto seleccionado sobre idénticos distritos. También están disponibles en el mapa Demografía, fichas, rankings y CSV para 2022 y 2026.

Fuente: SCB `FolkmDesoLandKon`, ambos sexos, categorías publicadas sv/eu/öv/tot. Europa incluye Rusia y Turquía; no es la UE ni la agrupación ONU municipal. Resto del mundo incluye desconocidos y no permite separar África/Asia. Los recuentos y denominador se transfieren con el cruce DeSO → distrito existente y después se calculan porcentajes. Son estimaciones de residentes, no recuentos observados por distrito ni composición de los electores. Se conservan protección estadística, ausentes y cobertura geométrica. No se fuerza una suma del 100 %.

Los constructores de 2022 y 2026 integran esta transformación automáticamente. Para añadir o reproducir solo estas columnas con los cruces ya calculados:

```sh
.venv/bin/python scripts/build_district_birth_regions.py
```

El comando comprueba que no se altere ninguna columna anterior. Cada edición publica `birth_regions_provenance.json`, con fuente, SHA-256 del original y del cruce, fechas y definiciones. `birth_regions_sum_gap` registra la diferencia estimada entre suma de componentes protegidos y total publicado.

## Tarjetas visuales y mapas categóricos

El hover ofrece distintivos tipográficos de partido (siglas y colores, no logotipos oficiales), ganador, tres primeros partidos, participación, votos y composición estimada de nacimiento fuera de Suecia. Las tarjetas municipales muestran los principales países o subtotales regionales. Las tarjetas se mantienen dentro del mapa; el clic abre el detalle completo.

- Partido ganador: `/?year=2026&view=electoral&metric=winning_party`.
- Bloque ganador: `/?year=2026&view=electoral&metric=winning_block`.
- Grupo de nacimiento extranjero predominante por distrito: `/?year=2026&view=demography&metric=common_origin`.
- País extranjero más común publicado por municipio: `/countries/?mode=common&country=SY`.
- Mayor subtotal continental publicado: `/countries/?mode=common&country=REG_AFRICA`.

Los bloques son agrupaciones analíticas explícitas y editables en config/blocks.json: S+V+MP+C / M+SD+KD+L para ambas ediciones. Se suman votos y se mantienen todos los votos válidos como denominador. No se denominan coaliciones oficiales. Otros partidos quedan fuera. Empates y datos pendientes tienen categorías propias.

El origen distrital compara únicamente Europa sin Suecia frente a resto del mundo con desconocidos (grupos SCB). La barra del hover divide entre la suma de ambos grupos, sin Suecia. Los porcentajes de los indicadores numéricos originales siguen usando todos los residentes estimados. Para municipios se excluyen Suecia y categorías agrupadas del ranking de países. Si la suma de celdas agrupadas/desconocidas podría superar al primer país, la categoría es indeterminada. El mapa regional compara cinco subtotales sin solapamientos; la mayor suma publicada no garantiza predominio real ante datos ocultos. Las descargas conservan categoría y definición.

## Nacimiento de los padres y definiciones de origen

La vista municipal ofrece «Nacimiento de los padres», con cuatro grupos SCB de 2025: nacidos fuera; nacidos en Suecia con ambos progenitores nacidos fuera; con uno nacido en Suecia y otro fuera; y con ambos nacidos en Suecia. Acceso directo: `/countries/?country=PARENT_MIXED`. Los filtros territoriales se conservan al llegar desde Origen. «Más común» no se aplica a estos grupos; se muestran proporciones sobre todos los residentes.

Fuente: SCB `UtlSvBakgFinCKM`, actualización 24/03/2026, referencia 31/12/2025. Se seleccionan `UtlBakgrund=TotUI,08,4,5,6`, `Alder=tot`, `Kon=TotSa`. Los 1.248 recuentos de cuatro grupos y los 312 denominadores proceden de las celdas publicadas para cada ámbito; no se suman municipios ni se mezclan los denominadores de la tabla de países. Se conserva la discrepancia entre suma de componentes y total causada por protección estadística CKM.

Reconstrucción: `.venv/bin/python scripts/build_parents.py`. También se ejecuta al final de `scripts/build_countries.py`. Archivos estáticos: `public/data/parents/background_2025.json.gz`, CSV y procedencia. La caché conserva petición, fecha y SHA-256.

El catálogo DeSO actual `BE0101Y` y los metadatos de `FolkmDesoBakgrKon` solo ofrecen origen sueco/extranjero, sin separar el grupo de un progenitor nacido fuera. No se reparten cifras municipales entre distritos. «Origen extranjero» SCB excluye a los nacidos en Suecia con solo un progenitor nacido fuera; ninguna de estas clases define ciudadanía, etnia o religión.

En Origen, «Qué mide este indicador» reúne las definiciones y un ejemplo sin ampliar el texto inicial. En Elecciones, los botones «Partido más votado» y «Bloque más votado» activan los mapas categóricos existentes; la ficha muestra ambos. «Más votado» no implica mayoría absoluta.

En Comparar, «Origen poblacional» controla el mapa izquierdo. El selector «Elecciones» dentro del mapa derecho admite Partido dominante, Bloque dominante y porcentaje de cada partido; está sincronizado con Partido en la barra superior. La URL conserva esta selección en `electionMetric`, sin alterar el indicador demográfico `metric`. Ejemplo: `/?view=compare&metric=foreign_background_pct&electionMetric=winning_block`. Cada mapa tiene su propia leyenda y hover.

## Evolución histórica

Abrir `http://localhost:5173/evolution/` o pulsar **Evolución** en el menú. Desde una ficha del atlas, **Ver evolución del municipio** conserva el municipio de ese distrito; desde Países también conserva el tipo de origen. La escala está indicada: Suecia o municipio completo, nunca una historia municipal asignada a un distrito actual.

- Votos: siete elecciones de 2002 a 2026, ocho partidos y otros. SCB hasta 2022; la instantánea firmada de Valmyndigheten de 2026 es provisional e incluye unidades de recogida cuando han informado. Se suman recuentos antes de dividir por votos válidos.
- Origen poblacional: 24 observaciones anuales, 2002–2025. Cuatro grupos por nacimiento propio/de padres, países de nacimiento y subtotales continentales ONU M49. Incluye el grupo nacido en Suecia con un progenitor nacido allí y otro fuera.
- Los botones de la leyenda ocultan/muestran líneas. El cursor y el selector de año muestran porcentajes; la tabla da una alternativa accesible. Se pueden elegir hasta ocho países. CSV exporta todos los recuentos, denominadores, porcentajes y ausencias del territorio.

Reproducir con los archivos municipales 2025 y la edición 2026 ya generados:

```sh
.venv/bin/python scripts/build_history.py
.venv/bin/python scripts/build_provenance.py
npm run build
```

El constructor descarga tablas oficiales SCB con peticiones y SHA-256 registrados en `data/raw/history/`; una segunda ejecución reutiliza y comprueba la caché. Verifica el hash del ZIP de 2026 contra el manifiesto de su importación firmada, la suma de votos, porcentajes frente a SCB, partición de los cuatro grupos hasta 2024, denominadores, intervalos y número de observaciones. Produce `public/data/history/index.json`, un JSON gzip por territorio y `provenance.json`. El navegador únicamente descarga estos archivos estáticos; no consulta SCB ni necesita un servicio adicional. `/evolution/index.html` también se genera para hospedaje estático en subdirectorios.

Límites: el origen de 2026 no está publicado y no se inventa; 2025 tiene protección CKM y se identifica mediante la etiqueta CKM. Las celdas de países agrupados/ocultos no se rellenan con ceros. Los continentes son subtotales de países publicados, y su cobertura puede variar; no son totales exhaustivos. Los códigos y el reconocimiento de países cambian. País de nacimiento no es religión ni etnia. Estos gráficos no miden el voto según origen individual.

SCB ya separa Knivsta en la elección de 2002; la población de 2002 utiliza la división de enero de 2003. La serie de Heby se publica con su código actual y el cambio de condado no cambia su extensión municipal. La transferencia entre Vaxholm y Lidingö se describe en las notas de comparabilidad: población de 2010 según división de enero de 2011, y tramo electoral 2010–2014. No se garantiza una geografía constante para todos los años.

Al seleccionar un distrito, su ficha abre simultáneamente la evolución electoral y de nacimiento a nivel distrital: archivo de votos 2002–2026 y población anual 2010–2025, según disponibilidad e identificación territorial. Usa Suecia, Europa excepto Suecia y resto del mundo + desconocido, las mismas categorías de la ficha distrital. Usa correspondencias oficiales para identificar unidades comparables; suma recuentos de 2022 para fusiones comparables y no asigna el nuevo distrito completo a un miembro antiguo aislado. Una unidad sin comparación válida conserva otras ediciones únicamente como referencia si se conserva el código dentro del municipio, con línea continua y notas de comparabilidad. El año inicialmente consultado coincide con la selección del atlas. La correspondencia electoral no significa que se haya recalculado la demografía histórica sobre un polígono fijo. Debajo de los datos del distrito hay una composición municipal separada, con población, año, continentes/padres y un enlace a la historia del municipio.

Las leyendas históricas usan tarjetas con fondo y borde del color de su línea. Pasar el cursor o enfocar una tarjeta destaca esa serie; pulsarla alterna su visibilidad. Los porcentajes parciales se etiquetan «Parcial» y el número de países/categorías sin publicación individual se conserva en el desplegable de cobertura. Al salir del gráfico se vuelve al año elegido con el selector (por defecto, el último); pulsar en el gráfico fija el año consultado. Los ejes terminan en el último año real de cada serie, 2025 para población y 2026 para votos.

Las tarjetas históricas usan fondos de color intenso, emblemas de partido y siluetas geográficas. El color de países/continentes se comparte con las tarjetas del mapa y permanece estable al añadir o quitar países. Los porcentajes se sitúan sobre una pastilla blanca y el texto de cada tarjeta elige negro/blanco según contraste. Créditos: `public/assets/credits.json`; reconstrucción: `.venv/bin/python scripts/build_visual_assets.py`.

La lógica de correspondencias y agregación distrital está en `src/utils/district-series.ts`. Los porcentajes se calculan sumando recuentos y sus denominadores, nunca promediando porcentajes. Una celda ausente se conserva como ausente; no se rellena usando datos municipales. La vista de evolución municipal independiente sigue disponible en `/evolution/`.


La ampliación distrital de 2018 se reproduce con `.venv/bin/python scripts/build_district_history.py` antes de `npm run build`. Descarga resultados definitivos de Valmyndigheten, sus polígonos y su correspondencia 2018–2022, y SCB DeSO y cuadrícula de población de 2018. Publica `public/data/history/districts_2018.json.gz` y su procedencia; no modifica el mapa de las ediciones 2022/2026. Verifica la partición completa de votos y los porcentajes oficiales antes de publicar. Las celdas electorales vacías solo se interpretan como cero al verificar que todas las celdas publicadas suman los votos válidos; las ausencias demográficas permanecen ausentes.

El archivo incorpora las siete elecciones de 2002 a 2026. Las correspondencias oficiales se usan desde 2014–2018; las ediciones anteriores con el mismo código se conservan como referencia, uniendo los puntos disponibles mediante líneas continuas y conservando las notas sobre comparabilidad. Se detiene la identificación automática si faltan tanto la correspondencia como el código, pero todos los distritos antiguos siguen accesibles en el archivo. El origen se publica año a año desde 2010, con valores ausentes explícitos en la consulta y la tabla por falta de estimación rigurosa. No se afirma que los límites se hayan mantenido constantes.

Para 2018 se conserva el mismo método espacial, con cuadrícula contemporánea y sin normalizar pesos. Se excluye una estimación si cualquier DeSO contribuyente asigna menos del 95 % o más del 101 % de su masa de población al conjunto de polígonos históricos; los identificadores excluidos y umbrales se publican en la procedencia. Los votos siguen disponibles aunque falte esa estimación poblacional. La composición y la evolución municipal se mantienen separadas.


Cuando un distrito conserva el código dentro del municipio pero no tiene correspondencia comparable, la ficha conserva sus ediciones como referencia. Todas las líneas conectan los puntos disponibles con trazo sólido, también a través de años sin dato y cambios territoriales o metodológicos. Las notas conservan esas diferencias. No se deduce comparabilidad por compartir código ni por la unión gráfica; no se sustituyen datos distritales por municipales.


## Archivo distrital completo disponible

En la ficha, **Explorar todos los distritos de cada elección** abre `/evolution/?scope=district&municipality=0180&year=2026&district=01803936`. Permite escoger municipio, elección y cualquier distrito publicado en esa edición. La historia municipal independiente sigue en `/evolution/`. Los archivos son estáticos y se descargan por municipio, no desde las APIs oficiales en el navegador.

Distritos físicos incorporados: 2002: 5.976; 2006: 5.783; 2010: 5.668; 2014: 5.837; 2018: 6.004; 2022: 6.264; 2026: 6.312. Se excluyen las unidades de recogida del mapa distrital. La validación de 2002 incluye esas unidades para contrastar con el total nacional antes de separarlas. SD se extrae del desglose oficial de otros partidos y se resta de Otros; no se convierte su ausencia de la tabla principal en un cero.

Reproducir, con las ediciones 2022/2026 y el histórico municipal ya generado:

```sh
.venv/bin/python scripts/build_district_history.py
.venv/bin/python scripts/build_district_2002.py
.venv/bin/python scripts/build_early_district_history.py
.venv/bin/python scripts/build_annual_district_birth.py
.venv/bin/python scripts/build_district_archive.py
.venv/bin/python scripts/build_provenance.py
npm run build
```

2002 conserva 7.003 páginas originales y verifica los recuentos nacionales de cada partido. Las importaciones 2006/2010/2014 verifican porcentajes oficiales y sumas. Los cruces geométricos procesados se reutilizan; para cambiarlos hay que regenerar el cruce correspondiente. Los originales llevan URL, fecha y SHA-256.

La población anual usa límites electorales de 2010 para 2010–2013, de 2014 para 2014–2017, de 2018 para 2018–2021, de 2022 para 2022–2024 y de 2026 para 2025. Hasta 2014 solo se publican uniones prácticamente completas de DeSO; desde 2015, estimaciones con cuadrícula del año correspondiente. No se publican repartos de población uniformes por superficie. El cambio a DeSO 2025 se marca en la observación de 2024; CKM se señala en 2025. La cobertura anual detallada se publica en `public/data/history/annual_district_birth_provenance.json`.

Los gráficos muestran el nombre, código y edición de los límites del año consultado, también en la tabla. Las líneas son continuas en todos los ámbitos y conectan los puntos disponibles, sin franjas ni tramos discontinuos. No se añaden observaciones, no se extrapola fuera de los puntos disponibles y los valores ausentes se mantienen en la consulta y la tabla. Con una sola observación se muestra un punto. Provisionalidad y CKM se conservan como etiquetas; las diferencias territoriales y metodológicas, como notas. Heby se agrupa en el archivo municipal actual 0331, conservando los identificadores distritales antiguos 1917; este agrupamiento no crea correspondencias distritales.

## Idiomas

El selector de la cabecera ofrece Español, English y Svenska en todas las rutas.
La elección se conserva en el navegador y puede compartirse con `?lang=es`,
`?lang=en` o `?lang=sv`; también se admiten los enlaces anteriores con `locale`.
Cambiar de idioma conserva los parámetros de la vista (distrito, filtros, cámara
u origen seleccionado). Los números y nombres de países usan el idioma elegido.

`src/i18n/messages.txt` contiene mensajes revisados en los tres idiomas, separados
por `|||`. La capa de presentación localiza texto y atributos accesibles de los
paneles dinámicos y los popups, sin modificar claves, datos o geometrías. Al añadir
texto visible, añadir también su traducción; las frases completas tienen prioridad
sobre fragmentos que acompañan cifras o nombres. Las fuentes originales y los
archivos de datos descargables conservan sus nombres y contenido de origen.

Validación: `npm test`; `PLAYWRIGHT_BROWSERS_PATH=.playwright npx playwright test
tests/e2e/language.spec.ts` después de compilar con `VITE_BASE_PATH=/atlas/`.


## Renta distrital · incorporación del 15/09/2026

El selector del atlas incorpora **Renta neta media anual · SEK ≈**, también en Comparar.
La ficha y el hover muestran el año propio de renta. En Análisis, el eje X permite elegir
renta y los indicadores numéricos de origen; la renta también está disponible como
control OLS. El eje X de renta usa miles de SEK/año, y la pendiente usa pp por 1.000 SEK.
Las escalas de color de renta usan P5–P95 nacionales redondeados a 10.000 SEK, sin
limitar importes al intervalo 0–100. El scatter conserva todos los valores extremos.

Fuente oficial: [SCB Tab1InkDesoRegso](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__HE__HE0110__HE0110I/Tab1InkDesoRegso/),
`InkomstTyp=NeInk`, `Kon=1+2`, media `0000089T`, personas `0000089O`.
La población de referencia es 20+ de año completo según las restricciones de SCB,
no todos los residentes ni los electores. Media de ingreso neto personal tras impuestos,
incluye capital y transferencias; no es salario, renta bruta, renta equivalente del hogar
ni mediana. La fuente publica tkr; se convierten a SEK. Ambas ediciones están en precios
constantes de **2024**. La instantánea de metadatos y datos está fijada al 15/09/2026.

- Mapa 2022: renta 2022, DeSO 2018, cuadrícula 2022; 6.259/6.264 distritos completos.
- Mapa 2026: renta 2024, DeSO y cuadrícula 2025, límites 2026; 6.312/6.312 completos.

Método: `sum(w * personas * media_tkr * 1000) / sum(w * personas)`.
Se reconstruyen sumas aproximadas a partir de medias redondeadas. La distribución de
personas 20+ e ingresos dentro de cada DeSO se supone igual a la de población total de
la cuadrícula: esto y el desfase 2024/2025/2026 añaden incertidumbre. Cualquier contribuyente
con peso positivo y media o personas ausentes deja el distrito sin renta. No se renormalizan
pesos ni se imputan ceros. Las medias agregadas usan los totales y personas transferidos.
No se construye una historia de renta sobre límites cambiantes.

Los constructores 2022 y 2026 adjuntan renta automáticamente. Para añadirla a los datos
existentes sin volver a generar votos o geometrías:

```sh
.venv/bin/python scripts/build_district_income.py
.venv/bin/python scripts/build_provenance.py
npm run build
```

Archivos: `public/data/{2022,2026}/income_provenance.json`, columnas `mean_net_income`,
`income_population`, `income_total_sek`, `income_year`, `income_price_year`, `income_complete`,
`income_method`, `income_deso_year`, `income_grid_year` e `income_source_url` en JSON/CSV.
Los demás campos se conservan sin cambios. La metodología web documenta también la historia
2002–2026, los puntos ausentes unidos visualmente, los cambios de límites y el contexto municipal separado.
