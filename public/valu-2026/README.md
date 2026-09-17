# SVT VALU 2026: gráficos de grupos de votantes

Lámina resumen y cuatro gráficos de barras, en español e inglés, PNG/PDF/SVG.
Fuente: https://www.svt.se/nyheter/sa-rostade-olika-valjargrupper-gr3b30
Datos exactos del widget público de SVT, almacenados en valu-2026-source.json.
El JSON conserva URL de bundle, fecha de descarga UTC y SHA-256 del bundle.

Reproducir: .venv/bin/python scripts/plot_valu_2026.py
Actualizar desde SVT: añadir --refresh. Esto puede cambiar las ponderaciones.

Los números son porcentajes dentro de cada grupo, no la composición del
electorado de cada partido. Son estimaciones nacionales de una encuesta,
no resultados administrativos, ni estimaciones para cada distrito.
La muestra total supera 13.000; no se han encontrado en este widget tamaños
por subgrupo, errores estándar ni diseño de varianza. No se inventan intervalos.
El artículo señala una reponderación al resultado provisional el 14/09 a las 11:30.
Se muestran ocho partidos; no se rellenan otros ni se renormalizan porcentajes.
Las cifras se redondean solo para las etiquetas (una cifra decimal).
En el resumen la intensidad usa la misma escala 0–50% en todas las celdas.

Origen es el lugar de crianza del votante y sus padres según SVT, no
ciudadanía, país de nacimiento ni religión. Extraeuropeo: la persona o al menos
un progenitor se crio fuera de Europa. Europa incluye otros países nórdicos.
Se mantienen las categorías publicadas sin inferir categorías más detalladas
ni suponer que las filas de origen permiten reconstruir grupos excluyentes.
Las categorías ocupacionales agrupan niveles directivos; empresarios y
agricultores se publican juntos. No representan todas las situaciones laborales.

Renta y religión: no se incorporan al no haberse confirmado tablas comparables
del voto de septiembre de 2026; no se mezclan con simpatía política preelectoral.

Firma: Creado por @Calcetinletal · https://x.com/Calcetinletal
