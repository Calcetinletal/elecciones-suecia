# SVT VALU 2026: gráficos de grupos de votantes

Lámina resumen y cuatro gráficos de barras, en español e inglés, PNG/PDF/SVG.
Fuente: https://www.svt.se/nyheter/sa-rostade-olika-valjargrupper-gr3b30
Datos exactos del widget público de SVT, almacenados en valu-2026-source.json.
El JSON conserva URL de bundle, fecha de descarga UTC y SHA-256 del bundle.

Reproducir: .venv/bin/python scripts/plot_valu_2026.py
Actualizar desde SVT: añadir --refresh. Esto puede cambiar las ponderaciones.

Los gráficos principales muestran un índice relativo: cada columna (partido)
suma 100 dentro de cada variable (sexo, edad, origen u ocupación).
Fórmula: 100 × porcentaje de voto al partido en el grupo / suma de esos
porcentajes entre los grupos mostrados de la misma variable.
Los grupos se tratan sin ponderarlos por su tamaño. Por tanto, NO describe
la composición demográfica del electorado de cada partido. Tampoco mezcla
los grupos de distintas variables dentro de un mismo denominador.
Las etiquetas se redondean a una cifra decimal por mayores restos para que
las columnas impresas sumen exactamente 100.0. Puede haber ajustes de 0.1
respecto al redondeo convencional. El color usa el mismo rango 0–100 de índice.
El JSON normalizado incluye índices exactos y etiquetas redondeadas, fórmula
y SHA-256 del archivo de datos originales. Los índices no son z-scores.

Los gráficos cuyo nombre termina en -vote-share conservan los porcentajes
de voto originales, sin transformar. La galería permite alternar ambos modos.
Estos porcentajes originales son dentro de cada grupo, no la composición
del electorado de cada partido. No se rellenan otros partidos ni se fuerzan
sus filas a sumar 100%. El color de estas láminas originales usa 0–50%.

Son estimaciones nacionales de una encuesta, no resultados administrativos,
ni estimaciones para cada distrito. La muestra total supera 13.000; este widget
no publica tamaños por subgrupo, errores estándar ni diseño de varianza.
No se inventan intervalos. SVT indica una reponderación al resultado
provisional el 14/09 a las 11:30.

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
