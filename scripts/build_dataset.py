"""Join observations and estimates, preserving source denominators and quality flags."""
from common import *
import pandas as pd
import numpy as np
import gzip

def aggregate_demography(demo,cw,year):
    rows=cw.merge(demo,on='deso_id',how='left',validate='many_to_one')
    cols=list(demo.columns.drop('deso_id'))
    for col in cols: rows[col]=rows[col]*rows.weight
    values=rows.groupby('district_id')[cols].sum(min_count=1)
    values['demography_coverage']=(rows.groupby('district_id').overlap_area.sum()/rows.groupby('district_id').district_area.first()).clip(0,1)
    values['demography_data_coverage']=rows.assign(known=rows.population.notna().astype(float)*rows.overlap_area).groupby('district_id').known.sum()/rows.groupby('district_id').overlap_area.sum()
    values['dominant_overlap_share']=rows.groupby('district_id').population.max()/values.population
    source_coverage=cw.groupby('deso_id').weight.sum().clip(0,1)
    rows['supported_population']=rows.population*rows.deso_id.map(source_coverage)
    values['source_allocation_coverage']=rows.groupby('district_id').supported_population.sum()/values.population
    values['demography_method']=rows.groupby('district_id').method.agg(lambda s:'areal_estimate' if s.eq('areal_estimate').all() else 'mixed_spatial_estimate' if s.eq('areal_estimate').any() else 'population_weighted_estimate')
    for metric,num,den in [('foreign_background','foreign_background_count','population'),('foreign_born','foreign_born_count','birth_population'),('foreign_citizens','foreign_citizens_count','citizenship_population'),('higher_education','higher_education_count','education_population'),('employment','employed_count','employment_population')]:
        values[metric+'_pct']=100*values[num]/values[den].replace(0,np.nan)
    values['demography_year']=year;values['source_year']=year;values['demography_geometry_year']=2018 if year==2022 else 2025;values['population_grid_year']=year
    values['education_year']=2022 if year==2022 else np.nan;values['employment_year']=2021 if year==2022 else np.nan
    values['median_income']=np.nan;values['age']=np.nan;values['urban_density']=np.nan
    values['coverage_quality']=np.where((values.demography_coverage>=.98)&(values.demography_data_coverage>=.99)&(values.source_allocation_coverage>=.98),'high_coverage','partial_coverage')
    values.loc[values.population<=0,cols+[c for c in values if c.endswith('_pct')]]=np.nan
    return values

def main():
    election=pd.read_csv(PROCESSED/'elections_2022.csv',dtype={'district_id':str,'municipality_code':str,'county_code':str})
    demo=pd.read_csv(PROCESSED/'deso_demography.csv',dtype={'deso_id':str})
    cw=pd.read_parquet(PROCESSED/'crosswalk_2022.parquet')
    values=aggregate_demography(demo,cw,2022)
    out=election.merge(values,on='district_id',how='left',validate='one_to_one')
    out['demography_method']=out.demography_method.fillna('missing')
    out['coverage_quality']=out.coverage_quality.fillna('missing')
    out['election_source']='Valmyndigheten: definitive Riksdag 2022'
    out['demography_source']='SCB: DeSO 2018 / population 2022 / employment 2021'
    out['election_source_url']=SOURCES['election_2022']
    out['demography_source_url']='https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__BE__BE0101__BE0101Y/FolkmDesoBakgrKon/'
    from build_district_birth_regions import attach_birth_regions
    out=attach_birth_regions(out,2022,cw)
    from build_district_income import attach_income
    out=attach_income(out,2022,cw)
    out=out.sort_values('district_id')
    out.to_csv(PROCESSED/'joined_2022.csv',index=False,float_format='%.6f')
    folder=PUBLIC/'2022';folder.mkdir(exist_ok=True)
    out.to_csv(folder/'joined_2022.csv',index=False,float_format='%.6f')
    payload=out.round(6).to_json(orient='records',force_ascii=False).encode()
    (folder/'districts.json.gz').write_bytes(gzip.compress(payload,mtime=0))
    existing=json.loads((PUBLIC/'manifest.json').read_text()) if (PUBLIC/'manifest.json').exists() else {'years':[]}
    retained_2026=next((y for y in existing['years'] if y['year']==2026),{'year':2026,'status':'awaiting_definitive_data','district_count':0})
    write_json(PUBLIC/'manifest.json',{'schema_version':1,'years':[{'year':2022,'status':'definitive','district_count':len(out),'table':'2022/districts.json.gz','geometry':'2022/districts.geojson.gz','demography_year':2022,'demography_geometry_year':2018,'grid_year':2022,'employment_year':2021},retained_2026],'built_from':'Official cached sources; see SOURCES.md and SOURCE_AUDIT.md'})
    print('Joined',len(out),'districts. Coverage:',out.coverage_quality.value_counts().to_dict(),flush=True)
if __name__=='__main__': main()
