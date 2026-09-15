# Validación de la edición entregada

Fecha: 14 de septiembre de 2026. Entorno de ejecución: Ubuntu 24.04 / WSL, Python 3.12 y Node 18.19.1; Node 22 recomendado y configurado para GitHub Actions por los requisitos de una dependencia de MapLibre.

- Pipeline completo `python make_data.py`: terminado con caché de originales, 6.264 filas y geometrías, sin errores bloqueantes.
- Diez páginas SVT de diez municipios: votos válidos, electores, participación y los ocho partidos coinciden dentro del redondeo. Ver MANUAL_CHECKS.md.
- Once pruebas TypeScript: correlaciones, rangos con empates, OLS, cuantiles, ausencia de datos, filtros y URL.
- Ocho pruebas Python: overlay real con ponderación poblacional, fallback areal, conservación de masa en geometrías controladas y barreras de comparabilidad 2026.
- Cuatro pruebas Playwright: mapas, comparación, filtros, selección, descarga, recarga de estado/cámara, análisis, rutas estáticas físicas y móvil de 390 px.
- La prueba principal de mapas bloquea toda petición externa al servidor local.
- Compilación con `/atlas/` como prefijo y servidor estático sin fallback SPA: rutas de atlas, analysis y methodology accesibles; rutas inexistentes devuelven 404.
- Revisión visual de mapa nacional, comparación de un distrito, análisis de participación y mapa móvil.

Incidencias corregidas durante las comprobaciones: interferencia del CSS de MapLibre con la altura del contenedor, normalización de estados URL, encuadre inicial y conservación de cámara al recargar un distrito seleccionado.

Limitaciones conocidas: demografía estimada, 77 distritos con cobertura parcial, empleo 2021, categorías SCB de nacimiento/ciudadanía con desconocidos, renta mediana/edad/densidad ausentes. Una cobertura alta no garantiza precisión local. El GeoJSON simplificado tiene cambios de superficie registrados; la copia analítica no usa esa simplificación.

2026: datos reales provisionales integrados. 6.312 filas y polígonos, 6.276 contabilizados y 36 pendientes; porcentajes electorales y participación contrastados con el JSON oficial. Firmas digitales verificadas. Demografía 2025 disponible para los 6.312 distritos, todos con cobertura alta según los diagnósticos (no implica exactitud). 5.036 diferencias electorales calculables con correspondencia oficial. Los 35 casos de dos distritos suman recuentos y denominadores. Los tests verifican rechazo de simulaciones, nulos, participación sin distritos pendientes, agregación y discrepancias de correspondencias.

Se han probado selección de 2026, año demográfico visible, pendientes en gris, comparación cartográfica, deltas, CSV, análisis con 6.276 puntos y controles socioeconómicos desactivados. Revisión visual de escritorio y móvil. Las cuatro pruebas Playwright pasan sobre `/atlas/` con un servidor estático. Total: 23 pruebas (11 TypeScript, 8 Python, 4 navegador).

Limitaciones 2026: provisional estático, demografía estimada 2025 con protección CKM; empleo y educación sin datos. Ver data_quality_report_2026.md para simplificación y reparaciones. GitHub Pages está configurado; esta copia no se ha subido ni desplegado en una cuenta remota.

## Corrección de carga local gzip

El servidor Vite envía los archivos .json.gz con Content-Encoding: gzip. Fetch entrega el cuerpo ya descomprimido; intentar descomprimirlo de nuevo impedía cargar datos y dejaba los selectores desactivados. El lector ahora comprueba los bytes recibidos y admite tanto gzip binario como JSON descomprimido por HTTP.

Tres pruebas adicionales comprueban ambas modalidades y los errores HTTP. Se verificaron carga 2026, mapas, filtros, selección, análisis y CSV contra el servidor Vite real en el puerto 5173, además de la entrega gzip binaria del servidor estático. No se modificaron los datos electorales ni demográficos.

## Vista municipal de países

17 pruebas TypeScript, incluidas proporciones por país, denominador poblacional, ausentes y categorías agrupadas. Una prueba de navegador específica verifica la ruta `/countries/`, 188 categorías, selección de España/Siria, filtros Stockholm/Malmö, URL, CSV, elementos geográficos renderizados y ausencia de desbordamiento horizontal a 390 px. Se comprueban también las cuatro pruebas previas del atlas. Datos: 290 municipios, 312 ámbitos publicados, 58.656 celdas país/ámbito; porcentajes en [0,100], recuentos no negativos, códigos únicos, igualdad de claves tabla/geometría y polígonos válidos. Mapshaper notificó seis intersecciones no reparadas; la validación final individual pasó, sin afirmar ausencia total de pequeños solapes entre polígonos.

## Regiones geográficas de nacimiento

18 pruebas TypeScript y 10 Python: se verifican proporciones, preservación de ausentes, ausencia de datos en un grupo completo, partición continental, excepciones históricas y reconstrucción de todos los subtotales/coberturas de los 312 ámbitos. La prueba específica de navegador verifica diez agrupaciones, África, filtros de Malmö, persistencia en URL, cambio de vuelta a 188 países, descarga con subtotal/cobertura y explicación de religión. Se revisan mapas renderizados y ausencia de desbordamiento móvil a 390 px. Las dos pruebas de países/regiones pasan también contra el Vite local real (puerto 5173).

Limitación: estas sumas parciales no sustituyen los totales continentales que SCB no publica en la tabla detallada. La interfaz, leyenda, ficha, metodología, CSV y clasificación lo señalan. La religión no se infiere del nacimiento.

Resultado final: 34 pruebas superadas (18 TypeScript, 10 Python y 6 navegador), incluidas las rutas estáticas con prefijo `/atlas/`. Compilación de producción y reconstrucción completa `scripts/build_countries.py` correctas. Revisión visual de regiones en escritorio y móvil. La reconstrucción conserva diez agrupaciones y 3.120 observaciones con cobertura.

## Regiones de nacimiento sobre distritos electorales

Se añadieron tres pruebas TypeScript para categorías, valores y persistencia de comparación; cuatro pruebas Python para agregación de recuentos/denominadores, ausentes, conservación de perturbaciones y reconstrucción de las estimaciones publicadas desde los cruces. Se verifican las 6.264 y 6.312 claves electorales y todos los porcentajes a seis decimales.

Los constructores completos de datos de 2022 y 2026 se ejecutaron desde la caché existente, incorporando las columnas nuevas y verificando nuevamente firmas y resultados 2026. El comando incremental comprueba la igualdad de todas las columnas previas antes de escribir. No se publican nuevas estimaciones continentales detalladas ni religiosas.

La prueba específica de navegador comprueba mapas de idéntica geografía, selección de categoría y partido, recarga, ficha, notas, CSV, cambio entre 2022/2026 y móvil. Se probó contra Vite local en 5173. La sincronización del test al cambiar de año se ajustó para esperar la nueva geometría antes de capturar pantalla.

Resultado final de esta ampliación: 42 pruebas superadas (21 TypeScript, 14 Python y 7 navegador). La suite completa de navegador pasó con rutas estáticas físicas y prefijo `/atlas/`. Compilación de producción correcta; revisión visual de comparación por distrito en escritorio y mapa móvil. Fuentes y método accesibles desde el aviso del indicador y las fichas. El despliegue remoto sigue pendiente; el servidor local permanece disponible en 5173.

## Hover visual y mapas categóricos

29 pruebas TypeScript y 9 pruebas de navegador superadas. Se verifican sumas de votos por bloque, denominador de votos válidos, empates, pendientes, grupos de nacimiento con Suecia excluida, nulos, categorías continentales sin solapamiento, países agrupados ambiguos y escape de nombres en HTML. Las pruebas de navegador cubren tarjetas reales sobre polígonos, tres distintivos de partido, barras de nacimiento, mapas categóricos de partido/bloque/origen, persistencia en URL, CSV y móvil. La suite completa pasa con prefijo `/atlas/` y servidor estático sin fallback.

La revisión visual detectó recorte de las tarjetas al aparecer junto al borde inferior: se corrigió fijando su posición dentro del mapa. Se corrigió también la interceptación del cursor por la propia tarjeta en pantallas estrechas, evitando parpadeo. Las capturas finales muestran tarjetas completas en escritorio y móvil. Los distintivos son siglas con colores propios, no logotipos oficiales. Los datos electorales originales no se modifican; las categorías derivadas se incluyen al cargar y exportar.

Los bloques analíticos son S+V+MP+C / M+SD+KD+L para 2022 y 2026, explícitos en la interfaz y config/blocks.json. El origen más común por distrito mantiene los dos grupos SCB; el detalle municipal permite país o mayor subtotal continental publicado. No se afirma que los subtotales incompletos determinen el verdadero predominio continental.

## Interfaz simplificada

Tarjetas de hover de 238 px en escritorio y 218 px en móvil, centradas en el indicador elegido. Avisos de una línea y detalles desplegables para fuentes, precisión, tablas completas, distribuciones y rankings. Tres vistas principales; controles adicionales en «Más mapas» y «Opciones». El selector de partido solo aparece en vistas donde interviene. Se conservan las etiquetas de provisionalidad, estimación y subtotales incompletos junto a los valores.

Validación: 29 pruebas TypeScript y 9 pruebas de navegador superadas; compilación estática con prefijo /atlas/ y compilación final de raíz correctas. Las pruebas verifican el tamaño del hover, apertura de notas y desglose, visibilidad contextual del partido, filtros, descarga, enlaces y escritorio/móvil. Revisión visual de las capturas finales; servidor local en http://localhost:5173/ verificado con respuesta 200. Los datos publicados no se modificaron.

## Definiciones, progenitores y accesos a ganadores

Se verificaron 30 pruebas TypeScript, 11 de navegador y la nueva prueba Python que compara los 1.248 recuentos de progenitores y los 312 denominadores con la respuesta oficial SCB. Se conservan discrepancias CKM entre componentes y total (la nacional es de una persona). Los ceros publicados de estos grupos siguen siendo cero, y los ausentes siguen siendo nulos.

La suite de navegador pasó con rutas estáticas bajo /atlas/. Cubre definiciones desplegables, enlace con municipio conservado, cuatro grupos de progenitores, denominador propio, CSV con fuente correcta, cambio entre países/regiones/progenitores y móvil. Comprueba también los botones directos de partido/bloque y ambos ganadores en la ficha. Se ajustaron las capturas para esperar a que terminase el renderizado del mapa; se revisaron las imágenes finales de escritorio y móvil. La reconstrucción de progenitores desde caché se repitió correctamente.

El detalle de progenitores se mantiene a escala municipal; el catálogo y los metadatos DeSO actuales no permiten aislar al grupo de un solo progenitor nacido fuera. Fuentes, definición y fecha 31/12/2025 accesibles en la interfaz y public/data/parents/provenance.json.

## Selector Partido: opciones dominantes

«Partido dominante» y «Bloque dominante» se incorporan como primeras opciones del selector Partido en Elecciones. El selector permanece visible en los mapas categóricos. Se conserva por separado el último partido individual seleccionado para que los mapas de porcentaje y comparación mantengan códigos de partido válidos. Los botones directos y el indicador se sincronizan con el desplegable y la URL.

Verificación de esta corrección: cinco pruebas de navegador superadas, incluyendo selección desde Partido, vuelta a un partido individual, URL y recarga, comparación demográfica y móvil sin desbordamiento. Revisión visual del selector visible y compilación de producción correcta.

## Actualización del recuento: 15/09/2026 00:06 (Estocolmo)

Nueva instantánea 2026-09-15_000643. Fuente provisional actualizada el 14/09/2026 a las 18:30:03. 6.312 de 6.312 distritos territoriales contabilizados; 0 pendientes. Se incorporan los 36 pendientes anteriores y no cambian los votos de los distritos ya informados. 16 empates entre partidos; ningún ganador sin determinar. El registro de diferencias está en public/data/2026/refresh_summary.json.

Se verificaron el índice MD5, las tres firmas RSA/SHA-256 y el SHA-256 local. Límites y correspondencias coinciden con los anteriores por SHA-256, por lo que se reutilizó el cruce espacial. El pipeline completo de construcción, simplificación y validación 2026 finalizó sin errores bloqueantes. Los datos demográficos conservan sus fuentes de 2025. Se inspeccionó el archivo firmado del escrutinio definitivo: 15 de 6.626 unidades informadas; se mantiene el provisional completo y su etiqueta.

Validación ejecutada: 15 pruebas Python y 30 pruebas TypeScript superadas; compilación de producción correcta. Las pruebas E2E actualizadas para el nuevo recuento NO se ejecutaron: la revisión automática rechazó dos solicitudes por considerar prohibida la comparación de partidos y bloques, incluso tras revisar y explicar el alcance factual y local de las pruebas. No se intentó eludir el rechazo. No se afirma revisión visual nueva de esta instantánea.

## Origen poblacional y elecciones en Comparar

El selector antes llamado Indicador pasa a «Origen poblacional» en Origen/Comparar y a «Resultado electoral» en Elecciones. Comparar incorpora un selector «Elecciones» dentro del mapa derecho, además del selector Partido superior. Ambos incluyen Partido dominante, Bloque dominante y cada partido individual. Los controles son independientes: `metric` conserva el origen y `electionMetric` guarda `party`, `winning_party` o `winning_block` para el mapa derecho. Las URLs antiguas conservan la comparación con porcentaje del partido seleccionado.

Se añaden leyendas separadas y el hover consulta el indicador de su propio mapa. La ficha de distrito muestra los dos ganadores también en Comparar. Enlace de ejemplo: `/?view=compare&metric=foreign_background_pct&electionMetric=winning_block`.

Verificación: compilación TypeScript y producción correctas; revisión estática de controles, eventos, estado, colores y leyendas. Se añadieron cuatro pruebas de estado y una prueba E2E para este flujo, pero NO se han ejecutado: la revisión automática rechazó `npm test` por contener comparaciones de partidos y bloques. Sigue pendiente la verificación de ejecución y presentación en navegador; no se intentó eludir ese bloqueo.

## Idiomas · 2026-09-15

Selector visible de Español, English y Svenska en todas las rutas. Conserva el
idioma en almacenamiento local y enlaces, y mantiene distrito, filtros, cámara y
selecciones históricas al cambiar. Los nombres de países y formatos numéricos se
localizan; la navegación utiliza rutas estables independientes del texto visible.

Validación: 38 pruebas unitarias, compilación con prefijo `/atlas/` y 14 pruebas de
navegador verificadas. Una aserción antigua del desglose distrital se actualizó para
comprobar los dos grupos de filas existentes y su apertura/cierre; volvió a pasar.
Se revisaron visualmente el selector móvil en sueco y ambas evoluciones en inglés.
También se revisaron los textos desplegados de las cinco páginas en inglés,
incluidas notas y metodología. No se modificaron datos ni cálculos estadísticos.
