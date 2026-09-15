"""Publish small, static municipal bundles containing the full district archive."""
from common import *
import gzip,collections
YEARS=[2002,2006,2010,2014,2018,2022,2026]
def read(path):return json.loads(gzip.decompress(path.read_bytes()))
def main():
 all_rows={};all_links={};regions={r['code']:r['name'] for r in json.loads((PUBLIC/'history/index.json').read_text())['regions'] if r['level']=='municipality'}
 for year in YEARS:
  data=read(PUBLIC/f'{year}/districts.json.gz') if year>=2022 else read(PUBLIC/f'history/districts_{year}.json.gz')['rows']
  if len({r['district_id'] for r in data})!=len(data):raise ValueError('Duplicate archive IDs')
  all_rows[year]=data
  for r in data:
   if r['municipality_code']=='1917':r['source_municipality_code']='1917';r['municipality_code']='0331'
   r.setdefault('municipality_name',regions.get(r['municipality_code'],r['municipality_code']))
 all_links[2026]={r['district_id']:r['comparison_old_ids'].split(';') for r in all_rows[2026] if r['comparison_status'] in ['comparable','comparable_aggregate']}
 all_links[2022]=read(PUBLIC/'history/districts_2018.json.gz')['previous'];all_links[2018]=read(PUBLIC/'history/districts_2014.json.gz')['previous']
 for y,links in all_links.items():
  old_by={r['district_id']:r for r in all_rows[YEARS[YEARS.index(y)-1]]};current={r['district_id']:r for r in all_rows[y]}
  for id,ids in links.items():
   if id not in current or len(ids)!=len(set(ids)) or any(i not in old_by or old_by[i]['municipality_code']!=current[id]['municipality_code'] for i in ids):raise ValueError(('Broken official link',y,id,ids))
 annual={}
 reasons={'historical_grid_unavailable':'Sin estimación: el distrito divide áreas DeSO y falta una cuadrícula contemporánea incorporada','insufficient_spatial_coverage':'Estimación excluida: cobertura geográfica insuficiente','missing_source_cell':'Estimación no disponible: faltan celdas de origen','before_small_area_series':'La fuente de origen por áreas pequeñas empieza en 2010'}
 for year in range(2010,2026):
  data=json.loads((PROCESSED/f'district_birth_annual_{year}.json').read_text());edition=data['geometry_year']
  for id,r in data['rows'].items():
   if r['method'] in reasons:r['unavailable_reason']=reasons[r['method']]
   annual.setdefault(edition,{}).setdefault(id,[]).append(r)
 keys=['district_id','district_name','municipality_code','municipality_name','election_year','election_status','valid_votes','demography_year','birth_regions_year','birth_regions_population','birth_regions_complete','birth_regions_method','election_source_url','comparison_source_url']+['vote_'+p for p in PARTIES]+[k+'_count' for k in ['born_sweden','born_europe_ex_sweden','born_rest_world_unknown']]
 root=PUBLIC/'history/district_archive';root.mkdir(parents=True,exist_ok=True);summary=[]
 for code in sorted({r['municipality_code'] for rows in all_rows.values() for r in rows}):
  editions={str(y):[{k:r[k] for k in keys if k in r} for r in rows if r['municipality_code']==code] for y,rows in all_rows.items()}
  ids={y:{r['district_id'] for r in rows} for y,rows in editions.items()}
  payload={'editions':editions,'links':{str(y):{id:old for id,old in links.items() if id in ids[str(y)]} for y,links in all_links.items()},'birth':{str(y):{id:rows for id,rows in records.items() if id in ids[str(y)]} for y,records in annual.items()}}
  encoded=json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode();(root/f'{code}.json.gz').write_bytes(gzip.compress(encoded,mtime=0))
  summary.append({'code':code,'name':regions.get(code,code),'counts':{y:len(r) for y,r in editions.items()}})
 write_json(root/'index.json',{'years':YEARS,'birth_years':list(range(2010,2026)),'regions':summary,'scope':'Every published district edition. A reused code is only a reference across a break unless official correspondence validates comparison. No observation invented for a district that cannot be identified in a past edition.'})
 print('Archive:',{y:len(r) for y,r in all_rows.items()},'municipal bundles',len(summary),'gz bytes',sum(p.stat().st_size for p in root.glob('*.gz')),flush=True)
if __name__=='__main__':main()
