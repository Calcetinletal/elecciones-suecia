"""Auditable SCB socioeconomic/age histories; no interpolation or municipal substitutes.

Requires the historical population-grid crosswalks already used by birthplace history.
Run: .venv/bin/python scripts/build_socio_history.py
"""
from common import *
from download_demography import jsonstat_frame
import pandas as pd
import numpy as np
import gzip,re,collections
from concurrent.futures import ThreadPoolExecutor

SNAPSHOT='2026-09-16'
TABLES={'income':'HE/HE0110/HE0110I/Tab1InkDesoRegso','education':'UF/UF0506/UF0506D/UtbSUNBefDesoRegso','education_new':'UF/UF0506/UF0506D/UtbSUNBefDesoRegsoN','employment':'AM/AM0210/AM0210G/ArRegDesoStatusN','age':'BE/BE0101/BE0101Y/FolkmDesoAldKon'}
ROOT_OUT=PUBLIC/'history/socio'
SPECS={
 'income':{'label':'Renta neta media','unit':'SEK','factor':1,'years':list(range(2011,2025)),'source':'income','universe':'20+ · población de año completo · precios de 2024'},
 'education':{'label':'Educación superior','unit':'%','factor':100,'years':list(range(2015,2026)),'source':'education','universe':'25–64 años hasta 2022; 25–65 desde 2023'},
 'employment':{'label':'Empleo','unit':'%','factor':100,'years':list(range(2020,2025)),'source':'employment','universe':'20–64 años · ocupados / población · BAS'},
 'unemployment':{'label':'Desempleo','unit':'%','factor':100,'years':list(range(2020,2025)),'source':'employment','universe':'20–64 años · desempleados / población activa · BAS'},
 'young':{'label':'Menores de 20 años','unit':'%','factor':100,'years':list(range(2010,2026)),'source':'age','universe':'0–19 años / todos los residentes'},
 'senior':{'label':'65 años o más','unit':'%','factor':100,'years':list(range(2010,2026)),'source':'age','universe':'65+ / todos los residentes'},
 'population':{'label':'Población total','unit':'personas','factor':1,'years':list(range(2010,2026)),'source':'age','universe':'Residentes a 31 de diciembre'},
}

def source_url(name):return 'https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__'+TABLES[name].rsplit('/',1)[0].replace('/','__')+'/'+TABLES[name].rsplit('/',1)[1]+'/'
def metadata(name):return json.loads(cache(SOURCES['api_base']+TABLES[name],f'scb/socio_history/{SNAPSHOT}/{name}_metadata.json').read_text())
def download(pair):
 name,year=pair;meta=metadata(name)
 if name=='income' and meta['variables'][-1]['values'][-1]!='2024':raise ValueError('Reaudit income price basis')
 pattern=r'\d{4}[ABC]\d{4}'+('_DeSO2025' if year>=2024 else '')
 select={'Kon':['1+2'],'Tid':[str(year)],'InkomstTyp':['NeInk']}
 if name=='income':select['ContentsCode']=['0000089T','0000089O']
 if name=='employment':select.update(Alder=['20-64'],ContentsCode=['0000089X','0000089W','0000089V','0000089Y'])
 if name=='age':select['Alder']=['totalt','-4','5-9','10-14','15-19','65-69','70-74','75-79','80-']
 query=[]
 for v in meta['variables']:
  vals=[x for x in v['values'] if re.fullmatch(pattern,x) or re.fullmatch(r'\d{2}|\d{4}',x)] if v['code']=='Region' else select.get(v['code'],v['values'])
  if not vals or not set(vals)<=set(v['values']):raise ValueError(('Invalid selection',name,v['code']))
  query.append({'code':v['code'],'selection':{'filter':'item','values':vals}})
 raw=cache(SOURCES['api_base']+TABLES[name],f'scb/socio_history/{SNAPSHOT}/{name}_{year}.json',{'query':query,'response':{'format':'json-stat2'}})
 dim='UtbildningsNiva' if name.startswith('education') else 'Alder' if name=='age' else 'ContentsCode'
 f=jsonstat_frame(json.loads(raw.read_text())).pivot(index='Region',columns=dim,values='value')
 f.index=f.index.str.replace('_DeSO2025','',regex=False);f.index.name='deso_id'
 def pair(n,d):return pd.DataFrame({'n':n,'d':d},index=f.index)
 if name=='income':out={'income':pair(f['0000089T']*1000*f['0000089O'],f['0000089O'])}
 elif name.startswith('education'):out={'education':pair(f[['5','6']].sum(axis=1,min_count=2),f.sum(axis=1,min_count=5))}
 elif name=='employment':out={'employment':pair(f['0000089X'],f['0000089Y']),'unemployment':pair(f['0000089W'],f['0000089V'])}
 else:out={'young':pair(f[['-4','5-9','10-14','15-19']].sum(axis=1,min_count=4),f['totalt']),'senior':pair(f[['65-69','70-74','75-79','80-']].sum(axis=1,min_count=4),f['totalt']),'population':pair(f['totalt'],1)}
 return year,out

def crosswalk(year):
 edition=2010 if year<2014 else 2014 if year<2018 else 2018 if year<2022 else 2022 if year<2025 else 2026
 file=f'crosswalk_{edition}_areal.parquet' if year<2015 else f'crosswalk_{edition}.parquet' if year in [2018,2022,2025] else f'crosswalk_history_{edition}_grid_{year}.parquet'
 return edition,PROCESSED/file

def estimate(frame,cw,whole=False,count=False):
 if frame.index.duplicated().any():raise ValueError('Duplicate source keys')
 if not np.isfinite(cw.weight).all() or (cw.weight<0).any():raise ValueError('Invalid weights')
 join=cw[cw.weight>0].merge(frame,left_on='deso_id',right_index=True,how='left',validate='many_to_one')
 ok=np.isfinite(join.n)&np.isfinite(join.d)&(join.d>0)&(join.n>=0)
 complete=ok.groupby(join.district_id).all()
 sums=cw.groupby('deso_id').weight.sum()
 bad_sources=set(sums[(sums<(0.99999 if whole else .95))|(sums>(1.00001 if whole else 1.01))].index)
 bad=set(cw.loc[cw.deso_id.isin(bad_sources)&(cw.weight>0),'district_id'])
 if whole:bad.update(cw.loc[(cw.weight>1e-5)&(cw.weight<.99999),'district_id'])
 out=pd.DataFrame({'n':join.n*join.weight,'d':join.d*join.weight,'district_id':join.district_id}).groupby('district_id')[['n','d']].sum(min_count=1)
 if count:out['d']=1
 out.loc[~complete|out.index.isin(bad),:]=np.nan
 return out

def packed(frame):return {id:[r.get('n'),r.get('d')] for id,r in json.loads(frame.round(6).to_json(orient='index')).items()}
def gz(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode(),mtime=0))
def main():
 tasks=[(name,int(y)) for name in TABLES for y in metadata(name)['variables'][-1]['values']]
 frames=collections.defaultdict(dict)
 with ThreadPoolExecutor(max_workers=2) as pool:
  for year,result in pool.map(download,tasks):frames[year].update(result)
 bundles={};coverage=[];latest={2022:{},2026:{}};hashes={}
 archives={p.stem.split('.')[0]:json.loads(gzip.decompress(p.read_bytes())) for p in (PUBLIC/'history/district_archive').glob('*.json.gz')}
 district_codes={int(y):{r['district_id']:code for code,a in archives.items() for r in a['editions'].get(y,[])} for y in ['2010','2014','2018','2022','2026']}
 for year,metrics in sorted(frames.items()):
  edition,path=crosswalk(year);cw=pd.read_parquet(path);hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
  for metric,frame in metrics.items():
   small=frame[frame.index.str.fullmatch(r'\d{4}[ABC]\d{4}')]
   if set(small.index)!=set(cw.deso_id):raise ValueError(('Crosswalk/source mismatch',year,metric))
   # Area rows are published SCB aggregates; BAS only has small areas, aggregated explicitly.
   area=frame[frame.index.str.fullmatch(r'\d{2}|\d{4}')].copy();area_method='scb_published'
   if area.empty:
    area_method='sum_deso'
    groups={'00':small};groups.update({code:small[small.index.str.startswith(code)] for code in {x[:4] for x in small.index}|{x[:2] for x in small.index}})
    area=pd.DataFrame({code:{c:g[c].sum(min_count=len(g)) for c in ['n','d']} for code,g in groups.items()}).T
   for code,nd in packed(area).items():
    bundle=bundles.setdefault(code,{'area':{},'districts':{}})
    bundle['area'].setdefault(metric,[]).append({'year':year,'n':nd[0],'d':nd[1],'method':area_method})
   result=estimate(small,cw,year<2015,metric=='population')
   for id,nd in packed(result).items():
    code=district_codes[edition][id];bundle=bundles.setdefault(code,{'area':{},'districts':{}})
    bundle['districts'].setdefault(str(edition),{}).setdefault(id,{}).setdefault(metric,[]).append({'year':year,'n':nd[0],'d':nd[1]})
   coverage.append({'metric':metric,'year':year,'geometry_year':edition,'available':int(result.n.notna().sum()),'districts':len(result)})
   # Supplements for the current maps. Keep all original electoral/income/origin columns untouched.
   for mapyear in [2022,2026]:
    target=min(mapyear,max(SPECS[metric]['years']))
    if year==target and metric not in ['income','population']:
     current_path=PROCESSED/f'crosswalk_{mapyear}.parquet';current_cw=pd.read_parquet(current_path)
     values=estimate(small,current_cw,count=False)
     for id,nd in packed(values).items():
      row=latest[mapyear].setdefault(id,{})
      row['socio_'+metric+'_pct']=100*nd[0]/nd[1] if nd[0] is not None and nd[1] else None
      row['socio_'+metric+'_year']=year
   print(metric,year,'available',int(result.n.notna().sum()),flush=True)
 for code,bundle in bundles.items():gz(ROOT_OUT/f'{code}.json.gz',bundle)
 for year,data in latest.items():gz(ROOT_OUT/f'current_{year}.json.gz',data)
 urls={name:source_url(name) for name in TABLES}
 for spec in SPECS.values():spec['url']=urls[spec['source']]
 write_json(ROOT_OUT/'index.json',{'snapshot':SNAPSHOT,'metrics':SPECS,'sources':urls,'areas':sorted(bundles),'price_year':2024})
 raw_sources=[{'file':str(p.relative_to(RAW)),**json.loads(p.read_text())} for p in sorted((RAW/f'scb/socio_history/{SNAPSHOT}').glob('*.metadata.json'))]
 write_json(ROOT_OUT/'provenance.json',{'raw_sources':raw_sources,'snapshot':SNAPSHOT,'coverage':coverage,'crosswalk_sha256':hashes,'sources':urls,'method':'Sum source numerators and each metric’s own denominators with historical population-grid weights, then divide. Income numerator = rounded mean * persons. Population is a count, not a rate. Positive-weight missing contributors suppress the estimate. 2010–2014 only unions of effectively whole DeSO; annual grids from 2015. Historical electoral boundaries follow birthplace history. Current supplements use their map crosswalk (2022 grid for 2022, 2025 grid for 2026); employment 2024 on the 2026 map is estimated with 2025 weights. No missing-year interpolation, no municipal substitutions, no weighted medians.','breaks':['Education changes from ages 25–64 to 25–65 in 2023.','DeSO geography changes in 2024.','Age counts use CKM in 2025; components may not reconcile.','Employment and unemployment use BAS ages 20–64 only, 2020–2024; not spliced with RAMS.','District chains may change geography; reused IDs are reference observations, not proof of constant boundaries.','SCB education tables are official-source statistics, but their metadata do not designate this detailed table as official statistics.']})
 print('Published',len(bundles),'bundles; bytes',sum(p.stat().st_size for p in ROOT_OUT.glob('*.gz')),flush=True)
if __name__=='__main__':main()
