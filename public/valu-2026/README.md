# SVT VALU 2026: gráficos de grupos de votantes

Lámina resumen de cuatro variables y diez gráficos de barras, en español e inglés, PNG/PDF/SVG.
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
La composición que tiene como denominador todos los votantes de un partido
requiere recuentos conjuntos ponderados: 100 × votantes del grupo y del
partido / total de votantes del partido. No se obtiene normalizando estas
columnas. Faltan las bases ponderadas compatibles para calcularla en 2026.
Los tamaños muestrales de origen del PDF no se usan como sustituto: no se
confirma que sean las bases ponderadas de los porcentajes. Además, las
categorías familiares pueden solaparse. Las variables incompletas precisan
categorías restantes y sin respuesta para representar el total del partido.
Consulta de disponibilidad (17/09/2026): la colección de microdatos de VALU
en https://researchdata.se/sv/catalogue/collection/valu lista hasta 2024
(elecciones europeas) y 2022 (parlamentarias); no se localizó VALU 2026.
Las etiquetas se redondean a una cifra decimal por mayores restos para que
las columnas impresas sumen exactamente 100.0. Puede haber ajustes de 0.1
respecto al redondeo convencional. El color usa el mismo rango 0–100 de índice.
El JSON normalizado incluye índices exactos y etiquetas redondeadas, fórmula
y SHA-256 del archivo de datos originales. Los índices no son z-scores.

Los gráficos cuyo nombre termina en -row-normalized normalizan por filas:
100 × porcentaje del partido / suma de los ocho partidos dentro del grupo.
Cada fila suma 100.0, con redondeo por mayores restos a una cifra decimal.
Se excluye a «Otros»: el denominador son los ocho partidos mostrados, no
todos los votos. Se parte de los porcentajes originales, nunca del índice
normalizado por columnas. La intensidad usa la escala 0–50%, como la versión
original. El JSON valu-2026-row-normalized.json guarda valores exactos y
redondeados y el SHA-256 de la misma fuente.

Los gráficos cuyo nombre termina en -vote-share conservan los porcentajes
de voto originales, sin transformar. La galería permite alternar los tres modos.
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

Informe ampliado de SVT (15/09/2026): se añaden situación laboral, práctica
religiosa, estudios, sector público/privado, sindicatos y ocupación detallada.
Fuente: https://omoss.svt.se/download/18.c7d6c981a0a583535d1535/1789484134179/Valu%202026%20seminarium%20260915.pdf
La transcripción reproducible está en scripts/data/valu-2026-seminar.json,
copiada a la galería. Conserva etiquetas suecas, porcentajes originales de
los nueve grupos de partidos (incluido Otros), páginas y SHA-256 del PDF.
Se verificó visualmente contra las páginas 22, 23, 24 y 34. No se reemplazan
los datos originales del widget: cada gráfico identifica su propia fuente.
El informe está ponderado al resultado provisional de la noche electoral
(p. 1), y publica porcentajes enteros que pueden sumar algo más o menos de
100. Los modos normalizados operan sobre esos valores redondeados, sin
atribuirles mayor precisión estadística. --refresh solo actualiza el widget;
la transcripción del informe requiere una revisión explícita de la fuente.

Práctica religiosa significa frecuencia de asistencia a servicios/reuniones
de una iglesia o comunidad religiosa; no identifica confesiones. Nunca no
significa necesariamente ateísmo. No se infiere religión a partir del origen.
Situación laboral no incluye una fila específica de jubilados. Sindicatos
solo muestra LO/TCO/SACO; no incluye no afiliados. El sector público se
muestra como total, sin sumar sus subcategorías solapadas. Estas selecciones
no representan necesariamente a toda la población, y normalizar columnas
no permite reconstruir la composición del electorado.

No se ha confirmado en estas fuentes un desglose del voto por renta o por
confesión religiosa. No se mezcla con simpatía política preelectoral.

Firma: Creado por @Calcetinletal · https://x.com/Calcetinletal
