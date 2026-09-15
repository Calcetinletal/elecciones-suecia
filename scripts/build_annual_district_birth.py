"""Annual birthplace history, on the electoral boundaries of each historical edition."""
from build_early_district_history import geometry,birth_frame
from build_crosswalk import build
from build_district_birth_regions import estimate_birth_regions,GROUPS
from download_demography import jsonstat_frame
from common import *
import geopandas as gpd,pandas as pd,numpy as np,gzip,re

def records(path):return json.loads(gzip.decompress(path.read_bytes()))
def main():
 report=[]
 for year in range(2010,2026):
  edition=2010 if year<2014 else 2014 if year<2018 else 2018 if year<2022 else 2022 if year<2025 else 2026
  target=PROCESSED/f'district_birth_annual_{year}.json'
  if year in [2010,2014,2018,2022,2025]:
   raw=records(PUBLIC/f'{edition}/districts.json.gz') if edition>=2022 else records(PUBLIC/f'history/districts_{edition}.json.gz')['rows']
   out=pd.DataFrame(raw).set_index('district_id')
  else:
   cwpath=PROCESSED/(f'crosswalk_{edition}_areal.parquet' if year<2015 else f'crosswalk_history_{edition}_grid_{year}.parquet')
   if not cwpath.exists():
    g=geometry(edition) if edition<2018 else gpd.read_file(RAW/'history_district/boundaries_2018.zip').rename(columns={'VD':'district_id'}) if edition==2018 else gpd.read_parquet(PROCESSED/'boundaries_2022.parquet')
    deso=gpd.read_file(RAW/('scb/2025/deso_2025.gpkg' if year>=2024 else 'scb/deso_2018.gpkg')).rename(columns={'desokod':'deso_id'})
    grid=gpd.read_file(cache(SOURCES['grid_2022'].replace('2022',str(year)),f'scb/grid_{year}.gpkg'),columns=['beftotalt']).rename(columns={'beftotalt':'population'})
    build(deso,g,grid).to_parquet(cwpath,index=False)
   cw=pd.read_parquet(cwpath)
   if year<2024:frame=birth_frame(year)
   else:
    meta=json.loads((RAW/'history_district/birth_metadata.json').read_text());query=[]
    for v in meta['variables']:
     code=v['code'];values=[x for x in v['values'] if re.fullmatch(r'\d{4}[ABC]\d{4}_DeSO2025',x)] if code=='Region' else [str(year)] if code=='Tid' else ['1+2'] if code=='Kon' else [*GROUPS,'tot'] if code=='Fodelseregion' else v['values']
     query.append({'code':code,'selection':{'filter':'item','values':values}})
    p=cache(SOURCES['api_base']+SOURCES['tables']['birth'],f'history_full/birth_{year}.json',{'query':query,'response':{'format':'json-stat2'}})
    frame=jsonstat_frame(json.loads(p.read_text())).pivot(index='Region',columns='Fodelseregion',values='value');frame.index=frame.index.str.replace('_DeSO2025','',regex=False);frame.index.name='deso_id';frame=frame.reset_index()
   if set(frame.deso_id)!=set(cw.deso_id):raise ValueError('Source/crosswalk mismatch')
   out=estimate_birth_regions(frame,cw)
   sums=cw.groupby('deso_id').weight.sum()
   if year<2015:
    bad=set(cw.loc[(cw.weight>1e-5)&(cw.weight<.99999),'district_id']);bad_sources=set(sums[(sums<.99999)|(sums>1.00001)].index)
   else:bad=set();bad_sources=set(sums[(sums<.95)|(sums>1.01)].index)
   bad.update(cw.loc[(cw.weight>(1e-5 if year<2015 else 0))&cw.deso_id.isin(bad_sources),'district_id'])
   out.loc[out.index.isin(bad),[c for c in out if c!='birth_regions_complete']]=np.nan;out.loc[out.index.isin(bad),'birth_regions_complete']=False
   out['birth_regions_method']=np.where(out.index.isin(bad),'historical_grid_unavailable' if year<2015 else 'insufficient_spatial_coverage',np.where(out.birth_regions_complete,'whole_deso_estimate' if year<2015 else 'population_weighted_estimate','missing_source_cell'))
  payload={}
  for r in json.loads(out.reset_index().to_json(orient='records')):
   payload[r['district_id']]={'year':year,'population':r.get('birth_regions_population'),'counts':{key:r.get(key+'_count') for key in GROUPS.values()},'method':r.get('birth_regions_method'),'ckm':year==2025}
  for id,r in payload.items():
   n=r['population']
   if n is not None and (not np.isfinite(n) or n<0 or any(c is not None and (not np.isfinite(c) or c<0 or c>n+1e-5) for c in r['counts'].values())):raise ValueError(('Invalid annual estimate',year,id))
  write_json(target,{'geometry_year':edition,'rows':payload})
  report.append({'year':year,'geometry_year':edition,'districts':len(payload),'available':sum(r['population'] is not None for r in payload.values())})
  print('Annual birth',report[-1],flush=True)
 write_json(PUBLIC/'history/annual_district_birth_provenance.json',{'coverage':report,'method':'2010–2014 only unions of essentially whole DeSO; 2015 onward contemporaneous population-grid intersection weights. Each reference year uses boundaries of its electoral edition (2010, 2014, 2018, 2022; 2025 uses 2026 boundaries). Current map observations are reused exactly. No population before 2010. Territorial links and breaks inherited from the corresponding election-edition chain. No interpolation of missing observations. 2024 switches to DeSO 2025; 2025 introduces CKM.'})
if __name__=='__main__':main()
