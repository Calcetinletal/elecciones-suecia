"""Estimate SCB's three published DeSO birth regions on electoral polygons."""
from common import *
from download_demography import jsonstat_frame
import pandas as pd
import numpy as np
import gzip,re,argparse
SOURCE='https://www.statistikdatabasen.scb.se/pxweb/en/ssd/START__BE__BE0101__BE0101Y/FolkmDesoLandKon/'
GROUPS={'sv':'born_sweden','eu':'born_europe_ex_sweden','öv':'born_rest_world_unknown'}

def estimate_birth_regions(frame,crosswalk):
    if frame.deso_id.duplicated().any():raise ValueError('Duplicate DeSO')
    if not np.isfinite(crosswalk.weight).all() or (crosswalk.weight<0).any():raise ValueError('Invalid spatial weights')
    rows=crosswalk.merge(frame,on='deso_id',how='left',validate='many_to_one')
    rows=rows[rows.weight>0].copy()
    fields=['tot',*GROUPS]
    # Any missing contributor makes all three estimates unavailable for this district.
    # Never turn an unknown source cell into zero or renormalize remaining sources.
    complete=rows[fields].notna().all(axis=1)
    valid=complete.groupby(rows.district_id).all()
    totals=rows[fields].multiply(rows.weight,axis=0).groupby(rows.district_id).sum(min_count=1)
    totals.loc[~valid,:]=np.nan
    out=pd.DataFrame(index=totals.index);out['birth_regions_population']=totals['tot']
    for code,key in GROUPS.items():
        out[key+'_count']=totals[code]
        out[key+'_pct']=100*totals[code]/totals['tot'].where(totals['tot']>0)
    out['birth_regions_complete']=valid
    # Preserve the independent SCB cells; do not force their sum to equal the total.
    out['birth_regions_sum_gap']=totals[list(GROUPS)].sum(axis=1,min_count=3)-totals['tot']
    return out

def attach_birth_regions(out,election_year,crosswalk=None):
    year=2022 if election_year==2022 else 2025
    url=SOURCES['api_base']+SOURCES['tables']['birth']
    meta_path=cache(url,'scb/birth_metadata.json' if year==2022 else 'scb/2025/birth_metadata.json')
    meta=json.loads(meta_path.read_text());query=[]
    pattern=r'\d{4}[ABC]\d{4}' if year==2022 else r'\d{4}[ABC]\d{4}_DeSO2025'
    for variable in meta['variables']:
        code=variable['code']
        values=[v for v in variable['values'] if re.fullmatch(pattern,v)] if code=='Region' else [str(year)] if code=='Tid' else ['1+2'] if code=='Kon' else [*GROUPS,'tot'] if code=='Fodelseregion' else variable['values']
        if not values or not set(values)<=set(variable['values']):raise ValueError('Invalid selection '+code)
        query.append({'code':code,'selection':{'filter':'item','values':values}})
    raw=cache(url,f'scb/birth_regions_deso_{year}.json',{'query':query,'response':{'format':'json-stat2'}})
    frame=jsonstat_frame(json.loads(raw.read_text())).pivot(index='Region',columns='Fodelseregion',values='value')
    frame.index=frame.index.str.replace('_DeSO2025','',regex=False);frame.index.name='deso_id';frame=frame.reset_index()
    for code in GROUPS:
        if ((frame[code]<0)|(frame[code]>frame['tot'])).any():raise ValueError('Protected source count outside range: '+code)
    cw=pd.read_parquet(PROCESSED/f'crosswalk_{election_year}.parquet') if crosswalk is None else crosswalk
    if set(cw.deso_id)!=set(frame.deso_id):raise ValueError('DeSO source/crosswalk key mismatch')
    values=estimate_birth_regions(frame,cw)
    if set(values.index)!=set(out.district_id):raise ValueError('Electoral district key mismatch')
    added=[*values.columns,'birth_regions_method','birth_regions_year','birth_regions_source_url']
    result=out.drop(columns=[c for c in added if c in out]).merge(values,on='district_id',validate='one_to_one')
    result['birth_regions_method']=np.where(result.birth_regions_complete,result.demography_method,'missing_source_cell')
    result['birth_regions_year']=year;result['birth_regions_source_url']=SOURCE
    for key in GROUPS.values():
        if not result[key+'_pct'].dropna().between(0,100).all():raise ValueError('Estimate outside range')
    folder=PUBLIC/str(election_year)
    metadata=json.loads(raw.with_suffix('.json.metadata.json').read_text())
    write_json(folder/'birth_regions_provenance.json',{'source_url':SOURCE,'raw_sha256':metadata['sha256'],'downloaded_at':metadata['downloaded_at'],'reference_date':f'{year}-12-31','election_geometry_year':election_year,'deso_geometry_year':2018 if year==2022 else 2025,'deso_count':len(frame),'district_count':len(result),'complete_district_count':int(result.birth_regions_complete.sum()),'groups':GROUPS,'crosswalk_sha256':hashlib.sha256((PROCESSED/f'crosswalk_{election_year}.parquet').read_bytes()).hexdigest(),'method':'Transfer published counts and total with existing population-grid intersection weights, then divide. No municipal percentages. Missing source contributor means no district estimate. Weights are not renormalized.','definitions':['eu: Europe except Sweden, including Russia and Turkey, per SCB. Not the EU and not the municipal UN M49 grouping.','öv: rest of world including unknown birthplace. Not a clean non-European count; cannot separate Africa, Asia or religion.','Independent disclosure-controlled cells may not add to total. Sum gap retained; no forced normalization.','Geometric coverage and source allocation diagnostics are inherited from the electoral crosswalk. Same electoral polygon does not imply observed district demographic data.'],'max_abs_estimated_component_sum_gap':float(result.birth_regions_sum_gap.abs().max())})
    frame.to_csv(PROCESSED/f'deso_birth_regions_{year}.csv',index=False)
    print(f'Birth regions {election_year}: {len(frame)} DeSO -> {len(result)} districts; complete {int(result.birth_regions_complete.sum())}',flush=True)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--year',type=int,choices=[2022,2026]);args=parser.parse_args()
    for year in [args.year] if args.year else [2022,2026]:
        folder=PUBLIC/str(year);original=json.loads(gzip.decompress((folder/'districts.json.gz').read_bytes()))
        out=attach_birth_regions(pd.DataFrame(original),year).sort_values('district_id')
        payload=out.round(6).to_json(orient='records',force_ascii=False).encode()
        previous={r['district_id']:r for r in original}
        added={c for c in out if c.startswith('born_') or c.startswith('birth_regions_')}
        for row in json.loads(payload):
            if {k:v for k,v in row.items() if k not in added}!={k:v for k,v in previous[row['district_id']].items() if k not in added}:raise ValueError('Existing values changed')
        (folder/'districts.json.gz').write_bytes(gzip.compress(payload,mtime=0))
        for path in [folder/f'joined_{year}.csv',PROCESSED/f'joined_{year}.csv']:out.to_csv(path,index=False,float_format='%.6f')
if __name__=='__main__':main()
