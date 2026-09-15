"""Small stratified check against ten SVT pages, not a bulk scraper."""
from common import *
from urllib.parse import urljoin
import re,html
import pandas as pd

def links(h,base,digits):
    return list(dict.fromkeys(urljoin(base,html.unescape(x)) for x in re.findall(r'href="([^"]+)"',h) if re.search(r'riksdagsval-\d{'+str(digits)+r'}-',x)))
def num(s): return float(re.sub(r'[^\d,.-]','',html.unescape(s)).replace(',','.'))
def main():
    joined=pd.read_csv(PROCESSED/'joined_2022.csv',dtype={'district_id':str}).set_index('district_id')
    base='https://valresultat.svt.se/2022/'
    municipal=links(cache(base,'validation/national.html').read_text(),base,4)
    chosen=['0180','0380','0980','1280','1480','1880','2081','2281','2480','2584']
    checks=[]
    for code in chosen:
        url=next(u for u in municipal if 'riksdagsval-'+code+'-' in u)
        h=cache(url,f'validation/municipality_{code}.html').read_text()
        district_links=links(h,url,8)
        if not district_links:
            child=links(h,url,6)[0];h=cache(child,f'validation/constituency_{code}.html').read_text();district_links=links(h,child,8)
        # Middle of list to avoid always choosing the city centre.
        url=district_links[len(district_links)//2];id=re.search(r'riksdagsval-(\d{8})-',url)[1]
        h=cache(url,f'validation/district_{id}.html').read_text()
        d=joined.loc[id];record={'district_id':id,'district_name':d.district_name,'url':url}
        for label,key in [('Giltiga röster','valid_votes'),('Röstberättigade','eligible_voters'),('Valdeltagande','turnout_pct')]:
            m=re.search(re.escape(label)+r':\s*<b>([^<]+)</b>',h)
            if not m: raise ValueError(f'Cannot find {label} in {url}')
            record[key+'_svt']=num(m[1]);record[key+'_atlas']=float(d[key])
        for abbr in ['S','M','SD','V','C','KD','L','MP']:
            section=re.search(r'<li class="partymatch">(?:(?!</li>).)*?symbol-party-'+abbr.lower()+r'\s(?:(?!</li>).)*?</li>',h,re.S)
            if not section: raise ValueError('Party not found '+abbr)
            m=re.search(r'data-test_id="percentage-value-percent">([^<]+)',section[0]);record['pct_'+abbr+'_svt']=num(m[1]);record['pct_'+abbr+'_atlas']=float(d['pct_'+abbr])
        m=re.search(r'<strong>([\d,]+)% utländsk bakgrund',h)
        record['foreign_background_svt_2021']=num(m[1]) if m else None
        record['foreign_background_estimate_2022']=float(d.foreign_background_pct)
        record['election_pass']=all(abs(record[k+'_atlas']-record[k+'_svt'])<=.006 for k in ['turnout_pct']+['pct_'+p for p in ['S','M','SD','V','C','KD','L','MP']]) and all(record[k+'_atlas']==record[k+'_svt'] for k in ['valid_votes','eligible_voters'])
        checks.append(record)
    write_json(PROCESSED/'sample_checks.json',checks)
    lines=['# Comprobación de diez valdistrikt','', 'Fecha: 2026-09-14. Muestra en diez municipios. Se contrastan votos válidos, electores, participación y porcentajes de los ocho partidos parlamentarios contra las páginas de resultados definitivos SVT. Los votos proceden originalmente de Valmyndigheten. Tolerancia: 0,006 puntos para redondeo a dos decimales; recuentos idénticos.','', '**Demografía:** el dato mostrado por SVT (población/origen 2021) es exacto por distrito y redondeado; el atlas estima población/origen 2022 mediante DeSO. Se muestra la diferencia como diagnóstico, no como igualdad esperada ni validación de exactitud de la estimación.','', '| Distrito | Válidos: atlas / SVT | Participación: atlas / SVT | S: atlas / SVT | SD: atlas / SVT | Origen: estimación 2022 / SVT 2021 | Electoral |','|---|---|---|---|---|---|---|']
    for r in checks:
        lines.append(f"| [{r['district_id']} {r['district_name']}]({r['url']}) | {r['valid_votes_atlas']:.0f} / {r['valid_votes_svt']:.0f} | {r['turnout_pct_atlas']:.2f} / {r['turnout_pct_svt']:.2f} | {r['pct_S_atlas']:.2f} / {r['pct_S_svt']:.2f} | {r['pct_SD_atlas']:.2f} / {r['pct_SD_svt']:.2f} | {r['foreign_background_estimate_2022']:.2f} / {r['foreign_background_svt_2021']} | {'OK' if r['election_pass'] else 'REVISAR'} |")
    lines+=['','Los resultados estructurados completos (ocho partidos) están en `data/processed/sample_checks.json`; los HTML originales están en la caché local `data/raw/validation/`, sin redistribución.']
    (ROOT/'MANUAL_CHECKS.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines),flush=True)
    if not all(r['election_pass'] for r in checks): raise ValueError('Sample mismatch')
if __name__=='__main__': main()
