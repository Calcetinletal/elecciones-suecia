"""Import a normalized definitive 2026 release. Never infer comparability from codes."""
from common import *
from urllib.parse import urlparse
import argparse, gzip, shutil
import pandas as pd
import geopandas as gpd
import numpy as np
from validate_data import validate

STATUSES={'comparable','changed_boundary','new','removed'}

def compare(old,new,crosswalk):
    cw=crosswalk.fillna('').copy()
    required={'old_id','new_id','status','source_url'}
    if not required<=set(cw): raise ValueError('Crosswalk needs old_id,new_id,status,source_url')
    if not set(cw.status)<=STATUSES: raise ValueError('Unknown comparability status')
    for col,ids in [('old_id',set(old.district_id)),('new_id',set(new.district_id))]:
        values=cw.loc[cw[col]!='',col]
        if values.duplicated().any(): raise ValueError('Only explicit one-to-one comparisons supported; harmonize aggregates separately')
        if set(values)!=ids: raise ValueError(f'Crosswalk must classify every {col}, with no unknown codes')
    result=new.set_index('district_id').copy();previous=old.set_index('district_id')
    result['comparison_status']='new'
    for metric in ['pct_S','pct_SD','pct_M','turnout_pct']: result['delta_'+metric]=np.nan
    for r in cw.itertuples():
        if r.status=='removed':
            if not r.old_id or r.new_id: raise ValueError('removed requires only old_id')
            continue
        if r.status=='new':
            if r.old_id or not r.new_id: raise ValueError('new requires only new_id')
        elif not r.old_id or not r.new_id: raise ValueError('Comparison requires both IDs')
        result.loc[r.new_id,'comparison_status']=r.status
        result.loc[r.new_id,'comparison_source_url']=r.source_url
        if r.status=='comparable':
            host=urlparse(r.source_url).hostname or ''
            if host!='val.se' and not host.endswith('.val.se'): raise ValueError('Comparable rows require an official Valmyndigheten evidence URL')
            for metric in ['pct_S','pct_SD','pct_M','turnout_pct']:
                result.loc[r.new_id,'delta_'+metric]=result.loc[r.new_id,metric]-previous.loc[r.old_id,metric]
    return result.reset_index()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',type=Path,required=True,help='Normalized joined CSV, same core schema as 2022')
    p.add_argument('--geometry',type=Path,required=True,help='Validated simplified GeoJSON with district_id')
    p.add_argument('--comparability',type=Path,required=True)
    p.add_argument('--metadata',type=Path,required=True)
    args=p.parse_args();meta=json.loads(args.metadata.read_text(encoding='utf-8-sig'))
    if meta.get('election_year')!=2026 or meta.get('status')!='definitive': raise ValueError('Only definitive 2026 data accepted')
    for key in ['election_source_url','geometry_source_url','demography_source_url','license','downloaded_at']:
        if not meta.get(key): raise ValueError('Missing provenance: '+key)
    new=pd.read_csv(args.dataset,dtype={'district_id':str,'county_code':str,'municipality_code':str})
    if not new.election_year.eq(2026).all() or not new.geometry_year.eq(2026).all(): raise ValueError('Election and geometry must be 2026')
    observed=new.demography_method.eq('exact_valdistrikt')
    spatial=new.demography_method.isin(['population_weighted_estimate','areal_estimate','mixed_spatial_estimate'])
    if not (observed|spatial|new.demography_method.eq('missing')).all(): raise ValueError('Invalid method')
    if not new.loc[spatial,'demography_geometry_year'].eq(2025).all(): raise ValueError('2026 estimates must use DeSO 2025')
    if not new.loc[observed|spatial,'demography_year'].isin([2025,2026]).all(): raise ValueError('2026 demography must be 2025 or 2026')
    geo=gpd.read_file(args.geometry)
    errors,_=validate(new,geo)
    if errors: raise ValueError(json.dumps(errors))
    old=pd.read_csv(PROCESSED/'joined_2022.csv',dtype={'district_id':str})
    cw=pd.read_csv(args.comparability,dtype=str,keep_default_na=False)
    out=compare(old,new,cw)
    blocks=json.loads((ROOT/'config/blocks.json').read_text(encoding='utf-8-sig')).get('2026',{})
    for name,parties in blocks.items():
        if len(set(parties))!=len(parties) or not set(parties)<=set(PARTIES): raise ValueError('Invalid block parties')
        out[name]=out[[f'pct_{x}' for x in parties]].sum(axis=1)
    payload=geo.to_json(drop_id=True).encode()
    if len(payload)>20_000_000: raise ValueError('Simplify geometries or introduce PMTiles before importing')
    # All validation precedes writes. Keep input snapshots under immutable hashed names.
    folder=RAW/'imports/2026';folder.mkdir(parents=True,exist_ok=True)
    for source in [args.dataset,args.geometry,args.comparability,args.metadata]:
        content=source.read_bytes();digest=hashlib.sha256(content).hexdigest();dest=folder/(digest+source.suffix)
        if not dest.exists(): dest.write_bytes(content)
    target=PUBLIC/'2026';target.mkdir(exist_ok=True)
    out.to_csv(PROCESSED/'joined_2026.csv',index=False);out.to_csv(target/'joined_2026.csv',index=False)
    (target/'districts.json.gz').write_bytes(gzip.compress(out.to_json(orient='records',force_ascii=False).encode(),mtime=0))
    (target/'districts.geojson.gz').write_bytes(gzip.compress(payload,mtime=0))
    cw.to_csv(PROCESSED/'comparability_2022_2026.csv',index=False)
    write_json(target/'provenance.json',meta)
    manifest=json.loads((PUBLIC/'manifest.json').read_text())
    manifest['years']=[y for y in manifest['years'] if y['year']!=2026]+[{'year':2026,'status':'definitive','district_count':len(out),'table':'2026/districts.json.gz','geometry':'2026/districts.geojson.gz'}]
    write_json(PUBLIC/'manifest.json',manifest)
    print('Imported definitive 2026 dataset; comparable deltas:',int(out.comparison_status.eq('comparable').sum()))
if __name__=='__main__': main()
