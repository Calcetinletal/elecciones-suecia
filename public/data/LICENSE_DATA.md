# Licencias y condiciones de los datos

Auditadas el 14 de septiembre de 2026. La licencia del código no sustituye estas condiciones.

## Valmyndigheten

[Condiciones oficiales de datos abiertos](https://www.val.se/valresultat-och-statistik/statistik-och-data/om-var-oppna-data): uso, reutilización y redistribución libres, sin pago ni contrato, citando a Valmyndigheten. Se aplica atribución en cada mapa, fichas, metodología y este inventario. No se atribuye una licencia Creative Commons específica que la página no declara.

Archivos incluidos: resultados definitivos de Riksdag 2022 y geometrías electorales. Los ZIP provienen de las länsstyrelser y se publican en el catálogo de datos abiertos de Valmyndigheten.

## Statistics Sweden / SCB

[Datos abiertos](https://www.scb.se/vara-tjanster/oppna-data/), [condiciones de uso](https://www.scb.se/om-scb/om-scb.se-och-anvandningsvillkor): datos y geodatos abiertos bajo CC0 1.0 Universal. Se mantiene atribución voluntaria a SCB y se identifica la transformación como elaboración propia. El atlas no afirma colaboración oficial ni respaldo institucional.

Las estimaciones se derivan de tablas de población de SCB, DeSO 2018_v3 y cuadrícula de población 2022. Los datos de origen permanecen observaciones de DeSO; los datos por valdistrikt son estimaciones de este proyecto.

## SVT

Se inspeccionaron HTML, scripts y el payload estructurado del artículo de análisis de 2022. No se localizó una licencia explícita que permita redistribuir el conjunto íntegro encargado a SCB. Por ello **no se redistribuyen ni el JavaScript, ni el HTML, ni el dataset de SVT**. La caché de auditoría está excluida de git y de `public/`. Solo se documentan enlaces y una muestra mínima de diez comprobaciones numéricas.

## Código y bibliotecas

Código original: MIT, ver LICENSE. Dependencias sujetas a sus propias licencias, incluidas en los paquetes npm. El mapa no usa Mapbox, cartografía externa, claves API ni fuentes remotas. MapLibre GL JS es software independiente y abierto; algunos paquetes internos mantienen el prefijo histórico `@mapbox` sin implicar el uso de un servicio Mapbox.

## Al agregar nuevas fuentes

Documentar URL, fecha, licencia, año estadístico, año geográfico y transformaciones. No activar su publicación si las condiciones no permiten redistribución. Los formatos preparados para importar 2026 no autorizan a ignorar las condiciones de las fuentes futuras.

## Símbolos gráficos

Los emblemas de los partidos se guardan en `public/assets/parties/`, con procedencia individual y atribuciones en `public/assets/credits.json`. Cinco SVG están identificados como dominio público en sus fichas de Wikimedia Commons. Los emblemas S, SD y MP proceden de los sitios de esos partidos y se incluyen para identificación editorial; no forman parte de la licencia MIT del código. No se modifican sus colores ni geometría. Los símbolos actuales identifican las series históricas y no representan una cronología de cambios de marca.

Las siluetas de países y continentes proceden de Natural Earth 1:110m v5.1.2 (dominio público), simplificadas para iconos decorativos. Pueden omitir pequeñas islas; no alteran geometrías ni cifras estadísticas del atlas. Para categorías sin contorno disponible se usa un globo o silueta mundial genérica. En nacimiento y padres se usan pictogramas propios con Suecia/mundo. Constructor reproducible: `scripts/build_visual_assets.py`.
