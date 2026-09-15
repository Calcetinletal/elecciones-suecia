"""Import all pre-2018 downloadable district vote editions and conservative birth estimates."""
from common import *
from build_crosswalk import build
from build_district_birth_regions import estimate_birth_regions,GROUPS,SOURCE
from download_demography import jsonstat_frame
import geopandas as gpd,pandas as pd,numpy as np,gzip,zipfile,io,re
URLS={2014:'https://historik.val.se/val/val2014/statistik/2014_riksdagsval_per_valdistrikt.skv',2010:'https://historik.val.se/val/val2010/statistik/slutligt_valresultat_valdistrikt_R.skv'}
GEOMETRY={2014:'https://historik.val.se/val/val2014/statistik/gis/valgeografi_valdistrikt.zip',2010:'https://historik.val.se/val/val2010/statistik/gis/alla_valdistrikt.zip',2006:'https://historik.val.se/val/val2006/slutlig_ovrigt/statistik/kartor/riksdagen_i_valdistrikt.zip'}

def geometry(year):
 g=gpd.read_file(cache(GEOMETRY[year],f'history_full/geometry_{year}.zip')).rename(columns={'VD':'district_id','LKFV':'district_id','Lkfv':'district_id'})
 g=g.to_crs(3006);g.geometry=g.geometry.make_valid()
 if g.district_id.duplicated().any():g=g.dissolve(by='district_id',as_index=False)
 return g

def votes(year,g):
 if year==2006:
  z=zipfile.ZipFile(cache('https://historik.val.se/val/val2006/slutlig_ovrigt/statistik/riksdag/riksdagen_i_valdistrikt_excel.zip','history_full/votes_2006.zip'))
  x=pd.read_excel(io.BytesIO(z.read(z.namelist()[0])));x['district_id']=x.LKFV.astype(str).str.zfill(8);x=x[x.district_id.str.fullmatch(r'\d{8}')].copy()
  cols=[c for c in x if c.endswith('_ROST') and c not in ['TOT_ROST','BLANK_ROST']]
  x['valid_votes']=x[cols].sum(axis=1)
  if set(x.district_id)!=set(g.district_id):raise ValueError('2006 geometry/result mismatch')
  x=x.merge(g[['district_id','NAMN','KOM_NAMN']],on='district_id',suffixes=('_xls',''),validate='one_to_one')
  names=x.NAMN;municipal=x.KOM_NAMN;count_suffix='_ROST';pct_suffix='_PROC'
 else:
  x=pd.read_csv(cache(URLS[year],f'history_full/votes_{year}.skv'),sep=';',encoding='latin1',dtype=str)
  # Only four-character VALDIST values are territorial districts; two-character ones are collection units.
  x=x[x.VALDIST.str.fullmatch(r'\d{4}')].copy();x['district_id']=x.LAN.str.zfill(2)+x.KOM.str.zfill(2)+x.VALDIST
  x['valid_votes']=pd.to_numeric(x['Rost Giltiga']);names=x['Valdistrikt' if year==2014 else 'VALDISTRIKT'];municipal=x.KOMMUN;count_suffix=' tal';pct_suffix=' proc'
  cols=[c for c in x if c.endswith(' tal') and c not in ['BL tal','OG tal']]
  if not np.array_equal(x[cols].apply(pd.to_numeric).sum(axis=1),x.valid_votes):raise ValueError('Source vote partition '+str(year))
  if set(x.district_id)!=set(g.district_id):print('Geometry missing result IDs',year,len(set(x.district_id)-set(g.district_id)),flush=True)
 out=pd.DataFrame({'district_id':x.district_id,'district_name':names,'municipality_code':x.district_id.str[:4],'municipality_name':municipal,'election_year':year,'election_status':'definitive','valid_votes':x.valid_votes,'birth_regions_year':year,'demography_year':year})
 for p in PARTIES[:-1]:
  old='FP' if p=='L' else p
  out['vote_'+p]=pd.to_numeric(x[old+count_suffix])
  pct=pd.to_numeric(x[old+pct_suffix].astype(str).str.replace(',','.'))
  if ((100*out['vote_'+p]/out.valid_votes-pct).abs()>.00501).any():raise ValueError(('Percentage mismatch',year,p))
 out['vote_other']=out.valid_votes-out[['vote_'+p for p in PARTIES[:-1]]].sum(axis=1)
 if out.district_id.duplicated().any() or out[['vote_'+p for p in PARTIES]].isna().any().any() or (out[['vote_'+p for p in PARTIES]]<0).any().any():raise ValueError('Invalid results')
 return out

def birth_frame(year):
 url=SOURCES['api_base']+SOURCES['tables']['birth'];meta=json.loads((RAW/'history_district/birth_metadata.json').read_text());query=[]
 for v in meta['variables']:
  code=v['code'];values=[x for x in v['values'] if re.fullmatch(r'\d{4}[ABC]\d{4}',x)] if code=='Region' else [str(year)] if code=='Tid' else ['1+2'] if code=='Kon' else [*GROUPS,'tot'] if code=='Fodelseregion' else v['values']
  query.append({'code':code,'selection':{'filter':'item','values':values}})
 p=cache(url,f'history_full/birth_{year}.json',{'query':query,'response':{'format':'json-stat2'}})
 f=jsonstat_frame(json.loads(p.read_text())).pivot(index='Region',columns='Fodelseregion',values='value');f.index.name='deso_id';return f.reset_index()

def early_birth(out,g,year):
 cwpath=PROCESSED/f'crosswalk_{year}_areal.parquet'
 if not cwpath.exists():build(gpd.read_file(RAW/'scb/deso_2018.gpkg').rename(columns={'desokod':'deso_id'}),g).to_parquet(cwpath,index=False)
 cw=pd.read_parquet(cwpath);birth=estimate_birth_regions(birth_frame(year),cw)
 # No contemporaneous population grid imported before 2015: retain only unions of essentially whole DeSO.
 partial=set(cw.loc[(cw.weight>1e-5)&(cw.weight<.99999),'district_id'])
 sums=cw.groupby('deso_id').weight.sum();bad=set(sums[(sums<.99999)|(sums>1.00001)].index)
 partial.update(cw.loc[(cw.weight>1e-5)&cw.deso_id.isin(bad),'district_id'])
 birth.loc[birth.index.isin(partial),[c for c in birth if c!='birth_regions_complete']]=np.nan
 birth.loc[birth.index.isin(partial),'birth_regions_complete']=False
 out=out.merge(birth,on='district_id',how='left',validate='one_to_one');out['birth_regions_complete']=out.birth_regions_complete.fillna(False)
 out['birth_regions_method']=np.where(out.birth_regions_complete,'whole_deso_estimate','historical_grid_unavailable');out['birth_regions_source_url']=SOURCE
 return out

def main():
 frames={};geometries={}
 for year in [2006,2010,2014]:
  g=geometry(year);geometries[year]=g;out=votes(year,g)
  if year>=2010:out=early_birth(out,g,year)
  else:out['birth_regions_method']='before_small_area_series';out['birth_regions_complete']=False
  frames[year]=out
 # Official 2014–2018 interpretation: O and S only; never multiply votes by mapping percentages.
 z=zipfile.ZipFile(cache('https://historik.val.se/val/val2018/statistik/mappning_2014_2018.zip','history_full/mapping_2014_2018.zip'))
 m=pd.read_csv(io.BytesIO(z.read('vd-mappning-2014-2018.skv')),sep=';',dtype=str,encoding='latin1');flags=pd.read_csv(io.BytesIO(z.read('vd-indelning-2018.skv')),sep=';',dtype=str,encoding='latin1')
 flags=dict(flags.itertuples(index=False,name=None));mapping={}
 for new,part in m.groupby(m.columns[1]):
  if flags.get(new) in ['O','S']:
   ids=part.iloc[:,0].tolist()
   if any(i not in set(frames[2014].district_id) for i in ids):raise ValueError('Mapping missing 2014 result')
   mapping[new]=ids
 for year,out in frames.items():
  payload={'year':year,'rows':json.loads(out.round(6).to_json(orient='records',force_ascii=False)),'previous':mapping if year==2014 else {},'source':'https://historik.val.se/val/val2018/statistik/' if year==2014 else GEOMETRY[year]}
  (PUBLIC/f'history/districts_{year}.json.gz').write_bytes(gzip.compress(json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode(),mtime=0))
  print('Published',year,len(out),'birth available',int(out.birth_regions_complete.sum()),flush=True)
 write_json(PUBLIC/'history/early_district_provenance.json',{'years':[2006,2010,2014],'vote_sources':URLS,'geometry_sources':GEOMETRY,'birth_source':SOURCE,'birth_method':'2010 and 2014: only districts matching unions of whole DeSO 2018 (fraction tolerance 0.00001); all partial DeSO allocations excluded because no contemporary population grid was imported. No area-uniform population estimates published. No origin observation before 2010.','comparability':'Official 2014–2018 flags O and S, summing whole counts. No comparability asserted for 2002–2006–2010–2014 merely from an unchanged code.'})
if __name__=='__main__':main()
