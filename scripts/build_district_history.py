"""Reproducible 2018 district observations and official 2018–2022 correspondence."""
from common import *
from build_crosswalk import build
from build_district_birth_regions import estimate_birth_regions, GROUPS, SOURCE
from download_demography import jsonstat_frame
import geopandas as gpd
import pandas as pd
import numpy as np
import gzip, re

VOTES='https://historik.val.se/val/val2018/statistik/2018_R_per_valdistrikt.xlsx'
COMPARISON='https://www.val.se/download/18.162047b519a91d0533119148/1666857349837/jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt-v2.xlsx'
GEOMETRY='https://historik.val.se/val/val2018/statistik/2018_valgeografi_valdistrikt.zip'

def main():
    original=cache(VOTES,'history_district/votes.xlsx')
    counts=pd.read_excel(original,sheet_name='R antal')
    counts=counts[counts['LÄNSKOD'].notna() & counts['VALDISTRIKTSKOD'].notna()].copy()
    counts['district_id']=counts.apply(lambda r:f"{int(r['LÄNSKOD']):02d}{int(r['KOMMUNKOD']):02d}{int(r['VALDISTRIKTSKOD']):04d}",axis=1)
    geometry=gpd.read_file(cache(GEOMETRY,'history_district/boundaries_2018.zip')).rename(columns={'VD':'district_id'})
    if geometry.district_id.duplicated().any():raise ValueError('Duplicate polygons')
    counts=counts[counts.district_id.isin(geometry.district_id)].copy()
    if counts.district_id.duplicated().any() or set(counts.district_id)!=set(geometry.district_id):raise ValueError('Results/geometry keys mismatch')
    out=pd.DataFrame({'district_id':counts.district_id,'district_name':counts['VALDISTRIKTSNAMN'],'municipality_code':counts.district_id.str[:4],'municipality_name':counts['KOMMUNNAMN'],'election_year':2018,'election_status':'definitive','valid_votes':pd.to_numeric(counts['RÖSTER GILTIGA']),'demography_year':2018,'birth_regions_year':2018})
    party_columns=list(counts.columns[counts.columns.get_loc('M'):counts.columns.get_loc('OGEJ')])
    if not np.array_equal(counts[party_columns].fillna(0).sum(axis=1),out.valid_votes):raise ValueError('Full source party partition mismatch')
    for party in PARTIES[:-1]:
        # Blank vote cells are zero only after the full published party partition is checked.
        out['vote_'+party]=pd.to_numeric(counts[party]).fillna(0)
        if out['vote_'+party].isna().any():raise ValueError('Missing major-party result '+party)
    out['vote_other']=out.valid_votes-out[['vote_'+p for p in PARTIES[:-1]]].sum(axis=1)
    if (out[['valid_votes',*['vote_'+p for p in PARTIES]]]<0).any().any():raise ValueError('Invalid votes')
    if not np.array_equal(out[['vote_'+p for p in PARTIES]].sum(axis=1),out.valid_votes):raise ValueError('Vote partition mismatch')
    percent=pd.read_excel(original,sheet_name='R procent')
    percent=percent[percent['LÄNSKOD'].notna() & percent['VALDISTRIKTSKOD'].notna()].copy()
    percent['district_id']=percent.apply(lambda r:f"{int(r['LÄNSKOD']):02d}{int(r['KOMMUNKOD']):02d}{int(r['VALDISTRIKTSKOD']):04d}",axis=1)
    percent=percent.set_index('district_id').loc[out.district_id]
    for party in PARTIES[:-1]:
        error=np.abs(100*out['vote_'+party].to_numpy()/out.valid_votes.to_numpy()-pd.to_numeric(percent[party]).fillna(0).to_numpy())
        if np.nanmax(error)>.00501:raise ValueError('Published percentage disagrees '+party)
    cwpath=PROCESSED/'crosswalk_2018.parquet'
    if not cwpath.exists():
        deso=gpd.read_file(RAW/'scb/deso_2018.gpkg').rename(columns={'desokod':'deso_id'})
        grid=gpd.read_file(cache(SOURCES['grid_2022'].replace('2022','2018'),'scb/grid_2018.gpkg'),columns=['beftotalt']).rename(columns={'beftotalt':'population'})
        build(deso,geometry,grid).to_parquet(cwpath,index=False)
    cw=pd.read_parquet(cwpath)
    url=SOURCES['api_base']+SOURCES['tables']['birth']
    meta=json.loads(cache(url,'history_district/birth_metadata.json').read_text());query=[]
    for variable in meta['variables']:
        code=variable['code']
        values=[v for v in variable['values'] if re.fullmatch(r'\d{4}[ABC]\d{4}',v)] if code=='Region' else ['2018'] if code=='Tid' else ['1+2'] if code=='Kon' else [*GROUPS,'tot'] if code=='Fodelseregion' else variable['values']
        if not values or not set(values)<=set(variable['values']):raise ValueError('Invalid query '+code)
        query.append({'code':code,'selection':{'filter':'item','values':values}})
    raw=cache(url,'history_district/birth_2018.json',{'query':query,'response':{'format':'json-stat2'}})
    frame=jsonstat_frame(json.loads(raw.read_text())).pivot(index='Region',columns='Fodelseregion',values='value');frame.index.name='deso_id';frame=frame.reset_index()
    if set(cw.deso_id)!=set(frame.deso_id):raise ValueError('DeSO mismatch')
    birth=estimate_birth_regions(frame,cw)
    # Do not publish a point if an contributing source loses >5% of its grid mass
    # at the historical polygon boundary, or is materially double allocated.
    source_coverage=cw.groupby('deso_id').weight.sum()
    bad_sources=set(source_coverage[(source_coverage<.95)|(source_coverage>1.01)].index)
    bad_districts=set(cw.loc[(cw.weight>0)&cw.deso_id.isin(bad_sources),'district_id'])
    birth.loc[birth.index.isin(bad_districts),[c for c in birth if c!='birth_regions_complete']]=np.nan
    birth.loc[birth.index.isin(bad_districts),'birth_regions_complete']=False
    if set(birth.index)!=set(out.district_id):raise ValueError('Birth district mismatch')
    out=out.merge(birth,on='district_id',validate='one_to_one')
    out['birth_regions_method']=np.where(out.district_id.isin(bad_districts),'insufficient_spatial_coverage',np.where(out.birth_regions_complete,'population_weighted_estimate','missing_source_cell'));out['birth_regions_source_url']=SOURCE
    for group in GROUPS.values():
        if not out[group+'_pct'].dropna().between(0,100).all():raise ValueError('Birth percentage outside range')
    mapping=pd.read_excel(cache(COMPARISON,'history_district/comparison.xlsx'),sheet_name='Fysiska valdistrikt',dtype=str)
    ids2022={r['district_id'] for r in json.loads(gzip.decompress((PUBLIC/'2022/districts.json.gz').read_bytes()))}
    if mapping.Kod_2022.duplicated().any() or set(mapping.Kod_2022)!=ids2022:raise ValueError('2022 mapping mismatch')
    links={}
    for row in mapping.to_dict('records'):
        if str(row['Jämförbart']).strip().lower()=='nej':continue
        ids=[str(row[k]).strip() for k in ['Valdistriktskod2018','Kod 2 2018','Kod 3 2018'] if pd.notna(row[k]) and str(row[k]).strip()]
        if not ids or len(ids)!=len(set(ids)) or any(i not in set(out.district_id) or i[:4]!=row['Kod_2022'][:4] for i in ids):raise ValueError('Invalid correspondence '+str(row))
        links[row['Kod_2022']]=ids
    payload={'rows':json.loads(out.round(6).to_json(orient='records',force_ascii=False)),'previous':links,'source':COMPARISON}
    target=PUBLIC/'history/districts_2018.json.gz';target.write_bytes(gzip.compress(json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode(),mtime=0))
    sums=cw.groupby('deso_id').weight.sum()
    provenance={'election_year':2018,'population_year':2018,'districts':len(out),'complete_birth_districts':int(out.birth_regions_complete.sum()),'excluded_spatial_districts':sorted(bad_districts),'source_coverage_threshold':[.95,1.01],'comparable_2022_districts':len(links),'sources':{p.name:json.loads(p.read_text()) for p in (RAW/'history_district').glob('*.metadata.json')},'deso_geometry':json.loads((RAW/'scb/deso_2018.gpkg.metadata.json').read_text()),'grid':json.loads((RAW/'scb/grid_2018.gpkg.metadata.json').read_text()),'crosswalk_sha256':hashlib.sha256(cwpath.read_bytes()).hexdigest(),'source_weight_range':[float(sums.min()),float(sums.max())],'fallback_intersections':int((cw.method=='areal_estimate').sum()),'method':'Published DeSO 2018 counts transferred to election polygons of 2018 using 2018 population-grid intersection weights. Protected missing cells retained; estimates excluded when any contributing DeSO allocates less than 95% or more than 101% of its grid mass across electoral polygons. Correspondence follows Valmyndigheten, which allows small boundary changes; chained correspondence is not proof of identical territory. Earlier editions are published by the district archive builders.'}
    write_json(PUBLIC/'history/districts_2018_provenance.json',provenance)
    print({k:v for k,v in provenance.items() if k not in ['sources','grid','deso_geometry','method','excluded_spatial_districts']},flush=True)

if __name__=='__main__':main()
