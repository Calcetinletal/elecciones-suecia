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
    assert np.all(a.sum(axis=1)<=100.01), 'No renormalisation or invented missing-party values'
    return a

def save(fig, stem):
    for ext in ['png','pdf','svg']:
        fig.savefig(OUT / f'{stem}.{ext}', dpi=190, facecolor=fig.get_facecolor())
    plt.close(fig)

def footer(fig, lang, definition=False):
    fig.text(.045,.026,'Creado por @Calcetinletal' if lang=='es' else 'Created by @Calcetinletal',weight='bold',size=12,color='#17384a',url='https://x.com/Calcetinletal')
    fig.text(.955,.026,'Fuente: SVT VALU 2026 · 17 sep 2026' if lang=='es' else 'Source: SVT VALU 2026 · 17 Sep 2026',ha='right',size=10,color='#516572',url=SOURCE)

for lang, li in [('es',2),('en',3)]:
    fig=plt.figure(figsize=(16,10),facecolor='#f4f7fa')
    fig.text(.045,.951,'Cómo votaron los distintos grupos' if lang=='es' else 'How different groups voted',size=27,weight='bold',color='#15394c')
    fig.text(.045,.913,'SUECIA 2026  ·  % de voto a cada partido dentro del grupo' if lang=='es' else 'SWEDEN 2026  ·  Party vote share within each group (%)',size=14,color='#516572')
    # Numbers make every estimate explicit; stronger colour means a larger share,
    # using the same 0–50% intensity mapping in all four panels.
    layouts=[(.045,.635,.435,.21),(.54,.555,.415,.29),(.045,.29,.435,.25),(.54,.225,.415,.25)]
    for idx,(group,rect) in enumerate(zip(groups,layouts)):
        key,keys,_,_=group
        a=values(keys); labels=group[li]
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
                strength=.10+.82*min(a[i,j]/50,1)
                rgb=np.array(to_rgb(c)); bg=1-(1-rgb)*strength
                ax.add_patch(Rectangle((j+.035,i+.045),.93,.91,facecolor=bg,edgecolor='white',linewidth=1))
                lum=np.dot(bg,[.2126,.7152,.0722])
                ax.text(j+.5,i+.5,f'{a[i,j]:.1f}',ha='center',va='center',size=14,weight='bold',color='white' if lum<.5 else '#143447')
    fig.text(.045,.158,definitions[lang],size=10,color='#516572',linespacing=1.5)
    fig.text(.045,.086,notes[lang],size=10,color='#516572',linespacing=1.5)
    footer(fig,lang); save(fig,f'VALU-2026-summary-{lang}')
    for idx,group in enumerate(groups):
        key,keys,_,_=group; a=values(keys); labels=group[li]
        fig,axes=plt.subplots(1,len(keys),figsize=(max(11,len(keys)*3.8),7.8),sharex=True,sharey=True,facecolor='#f4f7fa')
        axes=np.atleast_1d(axes)
        fig.subplots_adjust(left=.065,right=.965,top=.76,bottom=.29,wspace=.16)
        fig.text(.045,.92,f'Sweden 2026 · {titles[lang][idx]}' if lang=='en' else f'Suecia 2026 · {titles[lang][idx]}',size=25,weight='bold',color='#15394c')
        fig.text(.045,.865,'Party vote share within each group (%) · SVT VALU' if lang=='en' else '% de voto a cada partido dentro del grupo · SVT VALU',size=13,color='#516572')
        xmax=np.ceil((a.max()+4)/5)*5
        for i,(ax,label) in enumerate(zip(axes,labels)):
            ax.set_facecolor('#f4f7fa'); ax.barh(range(8),a[i],color=colors,height=.64,zorder=3)
            ax.set_title(label.replace(' y agricultores','\ny agricultores').replace(' and farmers','\nand farmers'),size=13,pad=16)
            ax.set_yticks(range(8),parties,size=12,weight='bold'); ax.set_ylim(7.7,-.7); ax.set_xlim(0,xmax)
            ax.xaxis.set_major_locator(MultipleLocator(10)); ax.xaxis.set_major_formatter(PercentFormatter(100,decimals=0))
            ax.grid(axis='x',color='#dae3eb',zorder=0); ax.tick_params(axis='both',length=0,labelcolor='#516572')
            for spine in ax.spines.values():spine.set_visible(False)
            for j,v in enumerate(a[i]):ax.text(v+.55,j,f'{v:.1f}%',va='center',size=12,weight='bold',color='#17384a')
        if key=='background':fig.text(.045,.195,definitions[lang].split(' Ocupaciones:')[0].split(' Occupational')[0],size=9.5,color='#516572')
        if key=='occupation':fig.text(.045,.195,'SVT combina roles directivos con su categoría laboral, y empresarios con agricultores.' if lang=='es' else 'SVT combines managerial roles with their occupational category, and business owners with farmers.',size=10,color='#516572')
        fig.text(.045,.10,notes[lang],size=9.5,color='#516572',linespacing=1.5)
        footer(fig,lang); save(fig,f'VALU-2026-{key}-{lang}')

readme='''# SVT VALU 2026: gráficos de grupos de votantes

Lámina resumen y cuatro gráficos de barras, en español e inglés, PNG/PDF/SVG.
Fuente: {source}
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
'''.format(source=SOURCE)
(OUT/'README.md').write_text(readme,encoding='utf-8')
with zipfile.ZipFile(OUT/'VALU-2026-charts.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):
        if p.suffix in {'.png','.pdf','.svg','.json','.md'}:z.write(p,p.name)
print(f'Created 10 charts in 3 formats, source snapshot, README and ZIP: {OUT}')
PUBLIC=ROOT/'public/valu-2026'
PUBLIC.mkdir(parents=True,exist_ok=True)
for p in OUT.iterdir():
    if p.suffix in {'.png','.pdf','.svg','.json','.md','.zip'}:shutil.copy2(p,PUBLIC/p.name)
gallery='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sweden 2026 · Voter groups · VALU</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f4f7fa;color:#17384a;font:16px system-ui,sans-serif}header,main,footer{max-width:1450px;margin:auto;padding:16px 24px}header{display:flex;align-items:center;gap:15px;flex-wrap:wrap}header a{color:inherit}h1{font-size:clamp(23px,3vw,34px);margin:0}p{line-height:1.55}nav{display:flex;gap:7px;flex-wrap:wrap;margin:18px 0}button,.download{border:1px solid #c4d3df;border-radius:9px;background:white;color:#17384a;padding:10px 14px;font:inherit;cursor:pointer;text-decoration:none}button[aria-pressed=true]{background:#17384a;color:white}.lang{margin-left:auto}figure{margin:0}img{display:block;width:100%;height:auto;border-radius:12px;border:1px solid #dce5ed}.downloads{display:flex;gap:8px;flex-wrap:wrap;margin:15px 0}summary{cursor:pointer;padding:12px 0;font-weight:600}a{color:#176393}footer{border-top:1px solid #dce5ed;font-size:14px}.tablewrap{overflow:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{padding:10px;border-bottom:1px solid #dce5ed;text-align:right}th:first-child{text-align:left}small{color:#526977}.notice{max-width:1000px}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #daab24;outline-offset:3px}@media(max-width:600px){header,main,footer{padding:14px}nav button{padding:8px 10px;font-size:14px}}
</style><header><a href="../">← Atlas</a><a href="https://x.com/Calcetinletal">Creado por @Calcetinletal</a><div class="lang"><button data-lang="es">🇪🇸 Español</button> <button data-lang="en">🇬🇧 English</button></div></header>
<main><h1 id="title"></h1><p id="intro" class="notice"></p><nav id="charts" aria-label="Charts"></nav><figure><img id="plot" width="3040" height="1900" alt=""></figure><div class="downloads"><a class="download" id="png">PNG</a><a class="download" id="pdf">PDF</a><a class="download" id="svg">SVG</a><a class="download" id="zip" href="VALU-2026-charts.zip">ZIP</a></div><details><summary id="tabletitle"></summary><div class="tablewrap" id="table"></div></details><details><summary id="methodtitle"></summary><p id="method"></p><p id="definition"></p><p id="missing"></p><p><a href="valu-2026-source.json">JSON</a> · <a href="README.md">README</a> · <a href="https://www.svt.se/nyheter/sa-rostade-olika-valjargrupper-gr3b30">SVT VALU 2026</a></p></details></main><footer>SVT VALU 2026 · <a href="https://x.com/Calcetinletal">@Calcetinletal</a></footer>
<script>
const data=__DATA__,groups=__GROUPS__,parties=__PARTIES__,notes=__NOTES__,definitions=__DEFINITIONS__;
const copy={es:{title:'Suecia 2026 · Cómo votaron los distintos grupos',intro:'Porcentaje de voto a cada partido dentro de cada grupo. Estimaciones nacionales de la encuesta SVT VALU; no son recuentos oficiales por grupo.',tabs:['Resumen','Sexo','Edad','Origen','Ocupación'],table:'Ver porcentajes en tabla',method:'Fuente y metodología',missing:'Renta y religión no se incluyen: no se han confirmado tablas comparables del voto de septiembre de 2026.',zip:'Descargar todo · ZIP'},en:{title:'Sweden 2026 · How different groups voted',intro:'Party vote share within each group. National estimates from the SVT VALU voter survey, not official ballot counts by group.',tabs:['Overview','Sex','Age','Background','Occupation'],table:'View percentages in a table',method:'Source and methodology',missing:'Income and religion are not included: comparable tables of the September 2026 vote have not been confirmed.',zip:'Download all · ZIP'}};
let params=new URLSearchParams(location.search),lang=params.get('lang')==='en'?'en':'es',chart=['summary','sex','age','background','occupation'].includes(params.get('chart'))?params.get('chart'):'summary';
function render(){const c=copy[lang],keys=['summary',...groups.map(g=>g[0])];document.documentElement.lang=lang;document.getElementById('title').textContent=c.title;document.getElementById('intro').textContent=c.intro;document.getElementById('charts').innerHTML=keys.map((k,i)=>`<button data-chart="${k}" aria-pressed="${chart===k}">${c.tabs[i]}</button>`).join('');document.querySelectorAll('[data-lang]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.lang===lang));const stem=`VALU-2026-${chart}-${lang}`;const img=document.getElementById('plot');img.src=stem+'.png';img.alt=c.tabs[keys.indexOf(chart)]+' · '+c.intro;img.style.aspectRatio=chart==='summary'?'1.6':'auto';img.removeAttribute('height');for(const ext of ['png','pdf','svg'])document.getElementById(ext).href=stem+'.'+ext;document.getElementById('zip').textContent=c.zip;document.getElementById('tabletitle').textContent=c.table;document.getElementById('methodtitle').textContent=c.method;document.getElementById('method').textContent=notes[lang];document.getElementById('definition').textContent=definitions[lang];document.getElementById('missing').textContent=c.missing;let rows=[];for(const g of groups.filter(g=>chart==='summary'||g[0]===chart))g[1].forEach((key,i)=>rows.push('<tr><th scope="row">'+g[lang==='es'?2:3][i]+'</th>'+parties.map(p=>'<td>'+(data.rows.find(r=>r.party.toUpperCase()===p)[key]*100).toFixed(1)+'%</td>').join('')+'</tr>'));document.getElementById('table').innerHTML='<table><thead><tr><th>'+(lang==='es'?'Grupo':'Group')+'</th>'+parties.map(p=>'<th scope="col">'+p+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table>';history.replaceState(null,'','?lang='+lang+'&chart='+chart)}
document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.lang)lang=b.dataset.lang;if(b.dataset.chart)chart=b.dataset.chart;render()});render();
</script></html>'''
for key,value in [('DATA',data),('GROUPS',groups),('PARTIES',parties),('NOTES',notes),('DEFINITIONS',definitions)]:gallery=gallery.replace('__'+key+'__',json.dumps(value,ensure_ascii=False))
(PUBLIC/'index.html').write_text(gallery,encoding='utf-8')
