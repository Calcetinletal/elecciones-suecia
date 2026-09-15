# Informe de calidad de datos

Fecha: 2026-09-14. Elección: Riksdag 2022.

- Distritos: 6264; geometrías: 6264; CRS web: EPSG:4326.
- Errores que bloquean la publicación: 0.
- Fichas electorales contrastadas con SVT: 10.
- Distritos con demografía disponible: 6264.
- Cobertura parcial: 77.
- Unidades de recogida sin territorio: 314, conservadas en `data/processed/non_geographic_results_2022.csv`, excluidas intencionalmente del mapa.

## Validaciones

Geometrías presentes/válidas/no vacías, CRS, claves únicas, anti-join en ambos sentidos, porcentajes [0,100], suma de partidos, recuentos enteros no negativos, identidad participación y porcentajes, missing demográfico, cobertura [0,1].

## Errores

{}

## Advertencias

{
  "partial_coverage": [
    "01200303",
    "03820208",
    "03820403",
    "04800025",
    "04810103",
    "04880102",
    "04880301",
    "05810214",
    "06430104",
    "06430105",
    "06430110",
    "06800138",
    "06800139",
    "06800141",
    "06800142",
    "06800212",
    "06800545",
    "06800760",
    "06800967",
    "06801069",
    "06802081",
    "06802082",
    "06802083",
    "06802085",
    "12330503",
    "12330504",
    "12330601",
    "12330602",
    "12330801",
    "12330802",
    "12330803",
    "12330804",
    "12330805",
    "12330901",
    "12330902",
    "12800102",
    "12800108",
    "12800109",
    "12800110",
    "12800128",
    "12800131",
    "12800133",
    "12800134",
    "12800135",
    "12800136",
    "12800314",
    "12800401",
    "12800404",
    "12800412",
    "12800419",
    "12800425",
    "12800429",
    "12800430",
    "12800431",
    "12800432",
    "12800433",
    "12820101",
    "12820102",
    "12820104",
    "12820116",
    "12820117",
    "12820201",
    "12820501",
    "12820801",
    "12820803",
    "12901502",
    "21840401",
    "21840701",
    "22800103",
    "22811004",
    "22811010",
    "24800445",
    "24800662",
    "24800663",
    "24800771",
    "24800991",
    "24800993"
  ],
  "median_income_missing": 6264
}

## Overlay y conservación de masa

Los pesos usan masa de la cuadrícula en la intersección dividida por masa en todo el DeSO. La suma puede ser inferior a 1 en costas, aguas o diferencias de límites; no se oculta renormalizando. Puede superar levemente 1 por solapes de los originales. Las cifras estimadas no deben tratarse como recuentos exactos.

{
  "intersections": 36061,
  "source_weight_min": 0.3553146225257718,
  "source_weight_max": 1.003268385075269,
  "sources_below_99pct": {
    "0643A0010": 0.9707069459991814,
    "0643A0020": 0.9360558902015615,
    "0643C1010": 0.9414080547075292,
    "0643C1030": 0.9892788376550271,
    "0680A0090": 0.9754945629156709,
    "0680A0100": 0.8603282427187109,
    "0680B4010": 0.9117372671158555,
    "0680B4020": 0.9824643375529835,
    "0680C1440": 0.6563612122931806,
    "0680C1470": 0.46933849233030356,
    "0680C1510": 0.8618594575472098,
    "0680C1520": 0.7032569288186131,
    "0680C1530": 0.3553146225257718,
    "0680C1540": 0.7629806215619417,
    "0680C1550": 0.9692660527745559,
    "0680C1570": 0.9553755318002373,
    "0680C1580": 0.9652160729813837,
    "1233B2010": 0.8904033764410424,
    "1233B2020": 0.9619011521694314,
    "1233B2030": 0.8241427386189295,
    "1233B2050": 0.810030139213129,
    "1233B2060": 0.8769953498349222,
    "1233B2070": 0.9311086865405356,
    "1233B2080": 0.9576537618609178,
    "1233B3010": 0.9155307565621772,
    "1233B3020": 0.9254392168612998,
    "1280C1030": 0.9805690517618543,
    "1280C1090": 0.974558415260271,
    "1280C1540": 0.8682725069361806,
    "1280C2080": 0.9177945612137786,
    "1280C2210": 0.9762219129326986,
    "1280C2320": 0.6073333748685134,
    "1280C2710": 0.7596980471314394,
    "1280C2850": 0.986502236423115,
    "1280C2870": 0.9321327456372215,
    "1280C2880": 0.9376389700568906,
    "1280C2900": 0.9045924942438451,
    "1280C2920": 0.9612307400497595,
    "1282A0010": 0.8759236629628985,
    "1282B2010": 0.9882606892751827,
    "1282C1030": 0.9764866460252688,
    "1282C1040": 0.8786259718227194,
    "1282C1090": 0.8760967383449533,
    "1282C1190": 0.8113414049404815,
    "1290B2010": 0.9845199331032812,
    "1290B2050": 0.9628696064387579,
    "1290B2060": 0.9849985832890547
  },
  "sources_above_101pct": {},
  "fallback_intersections": 0
}

## Simplificación web

Ensayos: 8 m superó 20 MB; 15 m produjo 15,58 MB sin comprimir y 3,98 MB gzip. Se eligió 15 m. Los límites compartidos se simplifican conjuntamente; snap de 1 cm y limpieza sin rellenar huecos. La copia analítica original se conserva. Los cambios de superficie más grandes se enumeran, no alteran el ETL ni los resultados.

{
  "post_rounding_repairs": 1,
  "tolerance_m": 15,
  "method": "mapshaper weighted shared arcs, keep-shapes",
  "bytes_uncompressed": 15581494,
  "bytes_gzip": 3981193,
  "invalid_geometries": 0,
  "p99_relative_area_change": 0.007635845270803808,
  "maximum_relative_area_change": 0.05567701920790193,
  "districts_area_change_above_1pct": {
    "01260305": 0.010517526858777734,
    "01270045": 0.05567701920790193,
    "01801311": 0.010848408236617361,
    "01801413": 0.015755744261573414,
    "01801417": 0.02346214988256316,
    "01801505": 0.010765110563505669,
    "01802523": 0.010569388612580334,
    "01802530": 0.010022832857885544,
    "01804217": 0.011732540611512313,
    "01840223": 0.014181965800944597,
    "01840241": 0.01575545333102126,
    "07810816": 0.01664056139775352,
    "10820104": 0.010132917759794184,
    "12800107": 0.012268397185387914,
    "12800124": 0.015040468066125806,
    "12800324": 0.013307723423075162,
    "12800625": 0.015164416570624117,
    "12812407": 0.014256025442254773,
    "14800127": 0.027294189662036318,
    "14800207": 0.010774234094604523,
    "14800312": 0.011305526762674723,
    "14800430": 0.011070978492976842,
    "14800444": 0.012385107702292593,
    "14800445": 0.013568265402826973,
    "14800508": 0.02536352448683332,
    "14800521": 0.01714600251246878,
    "14800529": 0.011318230257735021,
    "14800911": 0.011228871221674446,
    "14900376": 0.020678054220835216
  }
}

## Limitaciones de la muestra

Los diez controles electorales coinciden dentro del redondeo. En demografía se comparan estimaciones 2022 con observaciones SVT 2021, por lo que las discrepancias no son errores de unión automáticamente. En la muestra hay diferencias de varios puntos porcentuales (ver MANUAL_CHECKS.md). Esto evidencia que la interpolación no garantiza exactitud local.
