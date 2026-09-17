"""Reproducible standalone VALU voter-group charts. No atlas data are modified.

Run .venv/bin/python scripts/plot_valu_2026.py [--refresh]
The refresh extracts literal statistical records; it never executes remote JS.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import shutil
import urllib.request
import zipfile
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle
from matplotlib.ticker import PercentFormatter, MultipleLocator
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/valu-2026'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = 'https://www.svt.se/nyheter/sa-rostade-olika-valjargrupper-gr3b30'
WIDGET = 'https://australis.svt.se/quickshot/kross/widgets/lo7ut/webframe.html'
args = argparse.ArgumentParser()
args.add_argument('--refresh', action='store_true')
args.add_argument('--summary-only', action='store_true', help='Regenerate summary charts and gallery, retaining existing bar charts')
args.add_argument('--gallery-only', action='store_true', help='Refresh gallery, metadata and archive, retaining existing figures')
args.add_argument('--mode', choices=['all','normalized','raw','rows'], default='all')
args = args.parse_args()
snapshot = OUT / 'valu-2026-source.json'
archived_snapshot = ROOT / 'public/valu-2026/valu-2026-source.json'
if not snapshot.exists() and archived_snapshot.exists() and not args.refresh:
    shutil.copy2(archived_snapshot,snapshot)
if args.refresh or not snapshot.exists():
    html = urllib.request.urlopen(WIDGET).read().decode()
    bundle = re.search(r'src="([^"]+app_valjargrupper\.js)"', html).group(1)
    raw = urllib.request.urlopen(bundle).read()
    js = raw.decode()
    # The source contains an array of flat numeric/null records and party IDs.
    literal = re.search(r'\bkl=(\[\{.*?\}\]);const _l=', js).group(1)
    literal = re.sub(r'([{,])([A-Za-z_][A-Za-z_0-9]*):', r'\1"\2":', literal)
    literal = re.sub(r':\.(\d)', r':0.\1', literal)
    rows = [r for r in json.loads(literal) if r['year'] == 2026]
    assert len(rows) == 8 and {r['party'] for r in rows} == {'s','v','mp','c','l','m','kd','sd'}
    snapshot.write_text(json.dumps(dict(source=SOURCE, widget=WIDGET, bundle=bundle,
        retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        bundle_sha256=hashlib.sha256(raw).hexdigest(),
        weighting='SVT article: reweighted to preliminary results on 2026-09-14 at 11:30',
        unit='fraction of respondents with a valid answer within each voter group',
        rows=rows), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

data = json.loads(snapshot.read_text(encoding='utf-8'))
parties = ['S','V','MP','C','L','M','KD','SD']
colors = ['#cf3049','#96254b','#80a52b','#268659','#259bbb','#2074b6','#51469a','#d3a700']
by_party = {r['party'].upper():r for r in data['rows']}
groups = [
    ('sex',['women','men'],['Mujeres','Hombres'],['Women','Men']),
    ('age',['_18_21','_22_30','_31_64','_65'],['18–21 años','22–30 años','31–64 años','65+ años'],['18–21 years','22–30 years','31–64 years','65+ years']),
    ('background',['svensk_bakgrund','europeisk_bakgrund','utomeuropeisk_bakgrund'],['Sueco','Europeo','Extraeuropeo'],['Swedish','European','Non-European']),
    ('occupation',['tjansteman','arbetare','foretagare_jordbrukare'],['Empleados no manuales','Trabajadores manuales','Empresarios y agricultores'],['White-collar employees','Manual workers','Business owners and farmers']),
]
titles = {'es':['Sexo','Edad','Origen familiar*','Ocupación'], 'en':['Sex','Age','Family background*','Occupation']}
seminar_path = ROOT / 'scripts/data/valu-2026-seminar.json'
seminar = json.loads(seminar_path.read_text(encoding='utf-8'))
shutil.copy2(seminar_path, OUT / 'valu-2026-seminar.json')
extra_groups = {g['key']: g for g in seminar['groups']}
for g in seminar['groups']:
    keys = [g['key']+'_'+r['key'] for r in g['rows']]
    groups.append((g['key'],keys,[r['label_es'] for r in g['rows']],[r['label_en'] for r in g['rows']]))
    for lang in ['es','en']:titles[lang].append(g['title_'+lang])
    for key, row in zip(keys,g['rows']):
        assert len(row['percentages']) == 9 and abs(sum(row['percentages'])-100) <= 4.5
        for p in parties:by_party[p][key] = row['percentages'][seminar['parties'].index(p)] / 100
seminar_notes = {
 'es': 'SVT VALU · Informe ampliado, 15 sep 2026 · 13.709 respuestas en total; sin tamaños por subgrupo en estas tablas.\nPonderado al resultado provisional de la noche electoral. Porcentajes publicados como enteros; sumas aproximadas. Ocho partidos mostrados.',
 'en': 'SVT VALU · Extended report, 15 Sep 2026 · 13,709 responses overall; no subgroup sizes in these tables.\nWeighted to the preliminary election-night result. Published percentages rounded to integers; approximate totals. Eight parties shown.'}
def chart_notes(key,lang):
    return seminar_notes[lang] if key in extra_groups else notes[lang]
definitions = {
 'es': '* Origen: categorías de crianza del votante y sus padres de SVT. Extraeuropeo: el votante o al menos un progenitor se crio fuera de Europa.\nEuropa incluye los demás países nórdicos. No equivale a país de nacimiento ni a religión. Ocupaciones: SVT agrupa categorías directivas y agricultores/empresarios.',
 'en': '* Background: SVT categories based on where voters and their parents grew up. Non-European: the voter or at least one parent grew up outside Europe.\nEurope includes the other Nordic countries. This is not birthplace or religion. Occupational categories combine managerial roles and farmers/business owners.'}
notes = {
 'es': 'Encuesta nacional a votantes, no escrutinio por grupo · Más de 13.000 respuestas en total; no se publica aquí el tamaño de cada subgrupo.\nEstimaciones ponderadas al resultado provisional (14 sep., 11:30). Grupos pequeños: mayor incertidumbre. Ocho partidos; no se renormaliza a 100%.',
 'en': 'National voter survey, not a count of ballots by group · Over 13,000 responses overall; subgroup sample sizes are not supplied here.\nWeighted to preliminary results (14 Sep., 11:30). Smaller groups: greater uncertainty. Eight parties shown; shares are not rescaled to 100%.'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'svg.fonttype':'none','axes.titleweight':'bold'})

def values(keys):
    a = np.array([[by_party[p][k]*100 for p in parties] for k in keys])
    assert np.all(np.isfinite(a)) and np.all((a>=0)&(a<=100))
    # Eight rounded integer percentages can exceed 100 in the seminar PDF.
    # Keep them as published; the original widget uses unrounded fractions.
    for key, row in zip(keys,a):
        is_seminar=any(key.startswith(g+'_') for g in extra_groups)
        assert row.sum() <= (104.01 if is_seminar else 100.01), 'Unexpected vote-share total'
    return a

# Normalize separately within each variable: mixing age, sex, origin and
# occupation into one denominator would combine overlapping populations.
def normalized_values(keys,axis=0):
    a=values(keys)
    if axis==1:a=a.T
    totals=a.sum(axis=0)
    assert np.all(totals>0), 'An all-zero column has no defined relative index'
    exact=100*a/totals
    # Largest-remainder rounding makes printed columns sum to exactly 100.0.
    units=np.floor(exact*10).astype(int)
    for j in range(a.shape[1]):
        order=np.argsort(-(exact[:,j]*10-units[:,j]),kind='stable')
        units[order[:1000-units[:,j].sum()],j]+=1
    assert np.allclose(exact.sum(axis=0),100)
    assert np.all(units.sum(axis=0)==1000)
    return (exact.T,units.T/10) if axis==1 else (exact,units/10)
normalized={g[0]:dict(keys=g[1],exact=normalized_values(g[1])[0].tolist(),display=normalized_values(g[1])[1].tolist()) for g in groups}
(OUT/'valu-2026-normalized.json').write_text(json.dumps(dict(
    source_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),seminar_sha256=hashlib.sha256(seminar_path.read_bytes()).hexdigest(),parties=parties,
    formula='100 * party vote share in group / sum of that party vote shares across the displayed groups of this variable',
    interpretation='Relative index, not the demographic composition of a party electorate. Group sizes are not used.',
    rounding='Largest remainder to one decimal; displayed columns sum to exactly 100.0.',groups=normalized),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
row_normalized={g[0]:dict(keys=g[1],exact=normalized_values(g[1],1)[0].tolist(),display=normalized_values(g[1],1)[1].tolist()) for g in groups}
(OUT/'valu-2026-row-normalized.json').write_text(json.dumps(dict(
    source_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),seminar_sha256=hashlib.sha256(seminar_path.read_bytes()).hexdigest(),parties=parties,
    formula='100 * party vote share in group / sum of the eight displayed party vote shares in that same group',
    interpretation='Vote share renormalized among the eight displayed parties; other parties are excluded.',
    rounding='Largest remainder to one decimal; displayed rows sum to exactly 100.0.',groups=row_normalized),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
row_note={
 'es':'Porcentajes recalculados entre los ocho partidos mostrados; se excluye a «Otros». Los ocho partidos suman 100% en cada grupo.',
 'en':'Vote shares rescaled among the eight displayed parties; other parties are excluded. The eight parties sum to 100% within each group.'}
scale_note = {
 'es': 'Índice relativo sin ponderar el tamaño de los grupos. No representa la composición del electorado de cada partido.',
 'en': 'Relative index without weighting group sizes. It does not describe the composition of each party’s electorate.'}
notes={k:v.replace(' Ocho partidos; no se renormaliza a 100%.','').replace(' Eight parties shown; shares are not rescaled to 100%.','') for k,v in notes.items()}

def save(fig, stem):
    for ext in ['png','pdf','svg']:
        target=OUT / f'{stem}.{ext}'
        fig.savefig(target, dpi=190, facecolor=fig.get_facecolor())
        if ext=='svg':target.write_text('\n'.join(line.rstrip() for line in target.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
    plt.close(fig)

def footer(fig, lang, key=None):
    fig.text(.045,.026,'Creado por @Calcetinletal' if lang=='es' else 'Created by @Calcetinletal',weight='bold',size=12,color='#17384a',url='https://x.com/Calcetinletal')
    label='Fuente: SVT VALU 2026 · 17 sep 2026' if lang=='es' else 'Source: SVT VALU 2026 · 17 Sep 2026'
    source=SOURCE
    if key in extra_groups:
        label=('Fuente: SVT VALU · Informe 15 sep · p. ' if lang=='es' else 'Source: SVT VALU · 15 Sep report · p. ')+str(extra_groups[key]['page'])
        source=seminar['source']+'#page='+str(extra_groups[key]['page'])
    fig.text(.955,.026,label,ha='right',size=10,color='#516572',url=source)

for mode,lang,li in [(mode,lang,li) for mode in ['normalized','raw','rows'] if args.mode in ['all',mode] for lang,li in [('es',2),('en',3)]]:
    if args.gallery_only:continue
    raw=mode=='raw'; row_mode=mode=='rows'; percentage=raw or row_mode
    def plot_values(keys):return values(keys) if raw else normalized_values(keys,1 if row_mode else 0)[1]
    suffix='-vote-share' if raw else '-row-normalized' if row_mode else ''
    fig=plt.figure(figsize=(16,10),facecolor='#f4f7fa')
    heading=('Cómo votaron los distintos grupos' if lang=='es' else 'How different groups voted') if raw else ('Apoyo relativo por grupo' if lang=='es' else 'Relative party support by group')
    subtitle=('SUECIA 2026 · % de voto a cada partido dentro del grupo' if lang=='es' else 'SWEDEN 2026 · Party vote share within each group (%)') if raw else ('SUECIA 2026 · Cada columna suma 100 dentro de su bloque' if lang=='es' else 'SWEDEN 2026 · Each column sums to 100 within its panel')
    if row_mode:
        heading='Voto por grupo · ocho partidos' if lang=='es' else 'Vote by group · eight parties'
        subtitle='SUECIA 2026 · Los ocho partidos suman 100% en cada grupo' if lang=='es' else 'SWEDEN 2026 · The eight parties sum to 100% within each group'
    fig.text(.045,.951,heading,size=27,weight='bold',color='#15394c')
    fig.text(.045,.913,subtitle,size=14,color='#516572')
    fig.text(.045,.885,('Porcentajes originales de SVT · Ocho partidos; las filas pueden no sumar 100%.' if lang=='es' else 'Original SVT vote shares · Eight parties; rows may not sum to 100%.') if raw else row_note[lang] if row_mode else scale_note[lang],size=11,color='#516572')
    layouts=[(.045,.635,.435,.21),(.54,.555,.415,.29),(.045,.29,.435,.25),(.54,.225,.415,.25)]
    for idx,(group,rect) in enumerate(zip(groups,layouts)):
        key,keys,_,_=group
        a=plot_values(keys); labels=group[li]; intensity=np.minimum(a/(50 if percentage else 100),1)
        ax=fig.add_axes(rect); ax.set_xlim(-3.4,8); ax.set_ylim(len(keys)+.2,-.95); ax.axis('off')
        ax.text(-3.4,-1.12,titles[lang][idx],size=17,weight='bold',color='#15394c')
        for j,(p,c) in enumerate(zip(parties,colors)):
            ax.text(j+.5,-.5,p,ha='center',va='center',size=13,weight='bold',color=c)
        for i,label in enumerate(labels):
            if key=='occupation':
                label=label.replace(' no manuales','\nno manuales') if lang=='es' else label.replace(' employees','\nemployees').replace(' and farmers','\nand farmers')
                if lang=='es' and label.startswith('Trabajadores'):label=label.replace(' manuales','\nmanuales')
                label=label.replace(' y agricultores','\ny agricultores')
            ax.text(-.18,i+.5,label,ha='right',va='center',size=12,color='#233e50')
            for j,c in enumerate(colors):
                strength=.10+.82*intensity[i,j]
                rgb=np.array(to_rgb(c)); bg=1-(1-rgb)*strength
                ax.add_patch(Rectangle((j+.035,i+.045),.93,.91,facecolor=bg,edgecolor='white',linewidth=1))
                lum=np.dot(bg,[.2126,.7152,.0722])
                ax.text(j+.5,i+.5,f'{a[i,j]:.1f}',ha='center',va='center',size=14,weight='bold',color='white' if lum<.5 else '#143447')
    fig.text(.045,.158,definitions[lang],size=10,color='#516572',linespacing=1.5)
    fig.text(.045,.086,notes[lang],size=10,color='#516572',linespacing=1.5)
    footer(fig,lang); save(fig,f'VALU-2026-summary-{lang}{suffix}')
    if args.summary_only:continue
    for idx,group in enumerate(groups):
        key,keys,_,_=group; a=plot_values(keys); labels=group[li]
        two_rows=len(keys)>4
        fig,axes=plt.subplots(2 if two_rows else 1,3 if two_rows else len(keys),figsize=(14 if two_rows else max(11,len(keys)*3.8),11 if two_rows else 7.8),sharex=True,sharey=True,facecolor='#f4f7fa')
        axes=np.atleast_1d(axes).ravel()
        fig.subplots_adjust(left=.065,right=.965,top=.71 if key in extra_groups else .76,bottom=.29,wspace=.16,hspace=.7)
        fig.text(.045,.92,f'Sweden 2026 · {titles[lang][idx]}' if lang=='en' else f'Suecia 2026 · {titles[lang][idx]}',size=25,weight='bold',color='#15394c')
        sub=('Party vote share within each group (%) · SVT VALU' if lang=='en' else '% de voto a cada partido dentro del grupo · SVT VALU') if raw else ('Relative index · Each party sums to 100 across the groups shown' if lang=='en' else 'Índice relativo · Cada partido suma 100 entre los grupos mostrados')
        if row_mode:sub='Vote within each group · The eight parties sum to 100%' if lang=='en' else 'Voto dentro de cada grupo · Los ocho partidos suman 100%'
        fig.text(.045,.865,sub,size=13,color='#516572')
        if not raw:fig.text(.045,.815,row_note[lang] if row_mode else scale_note[lang],size=10,color='#516572')
        xmax=np.ceil((a.max()+4)/5)*5
        for i,(ax,label) in enumerate(zip(axes,labels)):
            ax.set_facecolor('#f4f7fa'); ax.barh(range(8),a[i],color=colors,height=.64,zorder=3)
            ax.set_title(textwrap.fill(label,26),size=13,pad=16)
            ax.set_yticks(range(8),parties,size=12,weight='bold'); ax.set_ylim(7.7,-.7); ax.set_xlim(0,xmax)
            ax.xaxis.set_major_locator(MultipleLocator(10))
            if percentage:ax.xaxis.set_major_formatter(PercentFormatter(100,decimals=0))
            ax.grid(axis='x',color='#dae3eb',zorder=0); ax.tick_params(axis='both',length=0,labelcolor='#516572')
            for spine in ax.spines.values():spine.set_visible(False)
            for j,v in enumerate(a[i]):ax.text(v+.55,j,f'{v:.1f}'+('%' if percentage else ''),va='center',size=12,weight='bold',color='#17384a')
        if key=='background':fig.text(.045,.195,definitions[lang].split(' Ocupaciones:')[0].split(' Occupational')[0],size=9.5,color='#516572')
        if key=='occupation':fig.text(.045,.195,'SVT combina roles directivos con su categoría laboral, y empresarios con agricultores.' if lang=='es' else 'SVT combines managerial roles with their occupational category, and business owners with farmers.',size=10,color='#516572')
        if key in extra_groups:
            fig.text(.045,.195,textwrap.fill(extra_groups[key]['definition_'+lang],140),size=9.5,color='#516572',linespacing=1.5)
        fig.text(.045,.10,chart_notes(key,lang),size=9.5,color='#516572',linespacing=1.5)
        footer(fig,lang,key); save(fig,f'VALU-2026-{key}-{lang}{suffix}')

readme='''# SVT VALU 2026: gráficos de grupos de votantes

Lámina resumen de cuatro variables y diez gráficos de barras, en español e inglés, PNG/PDF/SVG.
Fuente: {source}
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
Los ocho partidos suman 100.0 en cada grupo, con redondeo por mayores restos a una cifra decimal.
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
'''.format(source=SOURCE)
(OUT/'README.md').write_text(readme,encoding='utf-8')
with zipfile.ZipFile(OUT/'VALU-2026-charts.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):
        if p.suffix in {'.png','.pdf','.svg','.json','.md'}:z.write(p,p.name)
print(f'Created normalized and original charts in 3 formats, source snapshot, README and ZIP: {OUT}')
PUBLIC=ROOT/'public/valu-2026'
PUBLIC.mkdir(parents=True,exist_ok=True)
for p in OUT.iterdir():
    if p.suffix in {'.png','.pdf','.svg','.json','.md','.zip'}:shutil.copy2(p,PUBLIC/p.name)
gallery='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sweden 2026 · Voter groups · VALU</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f4f7fa;color:#17384a;font:16px system-ui,sans-serif}header,main,footer{max-width:1450px;margin:auto;padding:16px 24px}header{display:flex;align-items:center;gap:15px;flex-wrap:wrap}header a{color:inherit}h1{font-size:clamp(23px,3vw,34px);margin:0}p{line-height:1.55}nav{display:flex;gap:7px;flex-wrap:wrap;margin:18px 0}button,.download{border:1px solid #c4d3df;border-radius:9px;background:white;color:#17384a;padding:10px 14px;font:inherit;cursor:pointer;text-decoration:none}button[aria-pressed=true]{background:#17384a;color:white}.lang{margin-left:auto}figure{margin:0}img{display:block;width:100%;height:auto;border-radius:12px;border:1px solid #dce5ed}.downloads{display:flex;gap:8px;flex-wrap:wrap;margin:15px 0}summary{cursor:pointer;padding:12px 0;font-weight:600}a{color:#176393}footer{border-top:1px solid #dce5ed;font-size:14px}.tablewrap{overflow:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{padding:10px;border-bottom:1px solid #dce5ed;text-align:right}th:first-child{text-align:left}small{color:#526977}.notice{max-width:1000px}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #daab24;outline-offset:3px}@media(max-width:600px){header,main,footer{padding:14px}nav button{padding:8px 10px;font-size:14px}}
</style><header><a href="../">← Atlas</a><a href="https://x.com/Calcetinletal">Creado por @Calcetinletal</a><div class="lang"><button data-lang="es">🇪🇸 Español</button> <button data-lang="en">🇬🇧 English</button></div></header>
<main><h1 id="title"></h1><p id="intro" class="notice"></p><nav id="modes" aria-label="Metric"><button data-mode="rows"></button><button data-mode="normalized"></button><button data-mode="raw"></button></nav><nav id="charts" aria-label="Charts"></nav><p id="groupdefinition" class="notice"></p><p><a id="chartsource" target="_blank" rel="noopener"></a></p><figure><img id="plot" width="3040" height="1900" alt=""></figure><div class="downloads"><a class="download" id="png">PNG</a><a class="download" id="pdf">PDF</a><a class="download" id="svg">SVG</a><a class="download" id="zip" href="VALU-2026-charts.zip">ZIP</a></div><details><summary id="tabletitle"></summary><div class="tablewrap" id="table"></div></details><details><summary id="methodtitle"></summary><p id="method"></p><p id="definition"></p><p id="missing"></p><p><a href="valu-2026-source.json">JSON</a> · <a href="valu-2026-seminar.json">JSON · informe ampliado</a> · <a href="README.md">README</a> · <a href="https://www.svt.se/nyheter/sa-rostade-olika-valjargrupper-gr3b30">SVT VALU 2026</a></p></details></main><footer>SVT VALU 2026 · <a href="https://x.com/Calcetinletal">@Calcetinletal</a></footer>
<script>
const data=__DATA__,groups=__GROUPS__,parties=__PARTIES__,notes=__NOTES__,definitions=__DEFINITIONS__,scaleNote=__SCALE_NOTE__,normalized=__NORMALIZED__,rowNormalized=__ROW_NORMALIZED__,rowNote=__ROW_NOTE__,extraGroups=__EXTRA_GROUPS__,seminarNotes=__SEMINAR_NOTES__,seminarSource=__SEMINAR_SOURCE__,titles=__TITLES__;
const copy={es:{title:'Suecia 2026 · Cómo votaron los distintos grupos',intro:'Porcentaje de voto a cada partido dentro de cada grupo. Estimaciones nacionales de la encuesta SVT VALU; no son recuentos oficiales por grupo.',tabs:['Resumen básico',...titles.es],table:'Ver porcentajes en tabla',method:'Fuente y metodología',missing:'No se ha confirmado en estas fuentes un desglose del voto por renta o por confesión religiosa. La práctica religiosa mide asistencia, no identifica una religión.',zip:'Descargar todo · ZIP'},en:{title:'Sweden 2026 · How different groups voted',intro:'Party vote share within each group. National estimates from the SVT VALU voter survey, not official ballot counts by group.',tabs:['Basic overview',...titles.en],table:'View percentages in a table',method:'Source and methodology',missing:'These sources do not provide a confirmed vote breakdown by income or religious affiliation. Religious attendance measures participation, not which religion a voter follows.',zip:'Download all · ZIP'}};
const metricCopy={es:{title:'Suecia 2026 · Apoyo relativo por grupo',intro:'Índice relativo: cada partido suma 100 dentro de cada bloque. No pondera el tamaño de los grupos ni representa la composición del electorado de cada partido.',rows:'Por grupo · 100%',normalized:'Índice sin ponderar',raw:'% de voto original'},en:{title:'Sweden 2026 · Relative party support by group',intro:'Relative index: each party sums to 100 within each panel. It does not weight group sizes or describe the composition of each party’s electorate.',rows:'By group · 100%',normalized:'Unweighted index',raw:'Original vote share (%)'}};
let params=new URLSearchParams(location.search),lang=['en','sv'].includes(params.get('lang'))?'en':'es',mode=['raw','rows','normalized'].includes(params.get('mode'))?params.get('mode'):'rows',chart=['summary',...groups.map(g=>g[0])].includes(params.get('chart'))?params.get('chart'):'summary';
function render(){
 const c=copy[lang],m=metricCopy[lang],raw=mode==='raw',rowMode=mode==='rows',keys=['summary',...groups.map(g=>g[0])];
 const extra=extraGroups[chart],currentNotes=extra?seminarNotes[lang]:notes[lang];
 document.getElementById('groupdefinition').textContent=extra?extra['definition_'+lang]:chart==='background'?definitions[lang]:'';
 const sourceLink=document.getElementById('chartsource');
 sourceLink.href=extra?seminarSource+'#page='+extra.page:'https://www.svt.se/nyheter/sa-rostade-olika-valjargrupper-gr3b30';
 sourceLink.textContent=extra?(lang==='es'?'Informe SVT · 15 sep 2026 · página ':'SVT report · 15 Sep 2026 · page ')+extra.page:(lang==='es'?'Gráfica interactiva de SVT':'SVT interactive chart');
 document.documentElement.lang=lang;
 document.getElementById('title').textContent=rowMode?(lang==='es'?'Suecia 2026 · Voto dentro de cada grupo':'Sweden 2026 · Vote within each group'):raw?c.title:m.title;
 document.getElementById('intro').textContent=rowMode?rowNote[lang]:raw?c.intro:m.intro;
 document.getElementById('charts').innerHTML=keys.map((k,i)=>`<button data-chart="${k}" aria-pressed="${chart===k}">${c.tabs[i]}</button>`).join('');
 document.querySelectorAll('[data-lang]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.lang===lang));
 document.querySelectorAll('[data-mode]').forEach(b=>{b.setAttribute('aria-pressed',b.dataset.mode===mode);b.textContent=m[b.dataset.mode]});
 const stem=`VALU-2026-${chart}-${lang}${raw?'-vote-share':rowMode?'-row-normalized':''}`,img=document.getElementById('plot');
 img.src=stem+'.png?v=group100';img.alt=c.tabs[keys.indexOf(chart)]+' · '+(rowMode?rowNote[lang]:raw?c.intro:m.intro);
 img.style.aspectRatio=chart==='summary'?'1.6':'auto';img.removeAttribute('height');
 for(const ext of ['png','pdf','svg'])document.getElementById(ext).href=stem+'.'+ext+'?v=group100';
 document.getElementById('zip').textContent=c.zip;document.getElementById('zip').href='VALU-2026-charts.zip?v=group100';
 document.getElementById('tabletitle').textContent=lang==='es'?'Ver valores en tabla':'View values in a table';
 document.getElementById('methodtitle').textContent=c.method;
 document.getElementById('method').textContent=currentNotes+' '+scaleNote[lang]+(lang==='es'?' Índice = 100 × porcentaje del grupo / suma de porcentajes del partido dentro del bloque. Redondeo por mayores restos a una cifra decimal.':' Index = 100 × group vote share / sum of that party’s shares within the panel. Largest-remainder rounding to one decimal.');
 if(rowMode)document.getElementById('method').textContent=currentNotes+' '+rowNote[lang]+(lang==='es'?' Fórmula: 100 × porcentaje del partido / suma de los ocho partidos en el mismo grupo. Se parte de los datos originales y se redondea por mayores restos.':' Formula: 100 × party vote share / sum of the eight parties in the same group. Computed from original data with largest-remainder rounding.');
 if(raw)document.getElementById('method').textContent=currentNotes+(lang==='es'?' Porcentajes originales dentro de cada grupo, sin normalizar; se muestran ocho partidos.':' Original percentages within each group, without normalization; eight parties are shown.');
 document.getElementById('definition').textContent=extra?extra['definition_'+lang]:definitions[lang];
 document.getElementById('missing').textContent=c.missing+' '+(lang==='es'?'La composición del electorado de cada partido requiere dividir sus votantes de cada grupo entre todos sus votantes, usando los pesos de la encuesta. Las fuentes consultadas de 2026 no proporcionan las bases ponderadas compatibles para hacerlo. Normalizar columnas no sustituye ese cálculo.':'The composition of each party’s electorate requires dividing its voters in each group by all its voters, using survey weights. The checked 2026 sources do not provide compatible weighted bases for this calculation. Column normalization cannot replace it.');
 let rows=[];
 for(const g of groups.filter((g,i)=>chart==='summary'?i<4:g[0]===chart))g[1].forEach((key,i)=>rows.push('<tr data-group="'+g[0]+'"><th scope="row">'+g[lang==='es'?2:3][i]+'</th>'+parties.map((p,j)=>'<td>'+(raw?data.rows.find(r=>r.party.toUpperCase()===p)[key]*100:(rowMode?rowNormalized:normalized)[g[0]].display[i][j]).toFixed(1)+(raw||rowMode?'%':'')+'</td>').join('')+'</tr>'));
 document.getElementById('table').innerHTML='<table><caption>'+m[mode]+'</caption><thead><tr><th>'+(lang==='es'?'Grupo':'Group')+'</th>'+parties.map(p=>'<th scope="col">'+p+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table>';
 history.replaceState(null,'','?lang='+lang+'&chart='+chart+'&mode='+mode);
}
document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.lang)lang=b.dataset.lang;if(b.dataset.chart)chart=b.dataset.chart;if(b.dataset.mode)mode=b.dataset.mode;render()});render();
</script></html>'''
for key,value in [('DATA',data),('GROUPS',groups),('PARTIES',parties),('NOTES',notes),('DEFINITIONS',definitions),('SCALE_NOTE',scale_note),('NORMALIZED',normalized),('ROW_NORMALIZED',row_normalized),('ROW_NOTE',row_note),('EXTRA_GROUPS',extra_groups),('SEMINAR_NOTES',seminar_notes),('SEMINAR_SOURCE',seminar['source']),('TITLES',titles)]:gallery=gallery.replace('__'+key+'__',json.dumps(value,ensure_ascii=False))
(PUBLIC/'index.html').write_text(gallery,encoding='utf-8')
