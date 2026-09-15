"""Estimate mean net annual income on electoral polygons from audited SCB DeSO cells.

Run standalone after the 2022/2026 builds, or use attach_income in either pipeline.
The snapshot and 2024 price basis are pinned for reproducibility.
"""
from common import *
from download_demography import jsonstat_frame
import pandas as pd
import numpy as np
import gzip,re,argparse

SOURCE='https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__HE__HE0110__HE0110I/Tab1InkDesoRegso/'
API=SOURCES['api_base']+'HE/HE0110/HE0110I/Tab1InkDesoRegso'
SNAPSHOT='2026-09-15'
MEAN='0000089T'
COUNT='0000089O'
PRICE_YEAR=2024
FIELDS=['mean_net_income','income_population','income_total_sek','income_complete','income_year','income_price_year','income_deso_year','income_grid_year','income_method','income_source_url']

def estimate_income(frame,crosswalk):
    if frame.deso_id.duplicated().any():raise ValueError('Duplicate income source areas')
    if not np.isfinite(crosswalk.weight).all() or (crosswalk.weight<0).any():raise ValueError('Invalid income spatial weights')
    rows=crosswalk[crosswalk.weight>0].merge(frame,on='deso_id',how='left',validate='many_to_one')
    complete=np.isfinite(rows.income_mean_tkr)&np.isfinite(rows.income_persons)&(rows.income_persons>0)
    valid=complete.groupby(rows.district_id).all()
    # Reconstruct an approximate income sum from the published, rounded mean and
    # its OWN population. Neither medians nor all-age population are averaged.
    rows['income_population']=rows.weight*rows.income_persons
    rows['income_total_sek']=rows.income_population*rows.income_mean_tkr*1000
    result=rows.groupby('district_id')[['income_population','income_total_sek']].sum(min_count=1)
    result.loc[~valid,:]=np.nan
    result['mean_net_income']=result.income_total_sek/result.income_population.where(result.income_population>0)
    result['income_complete']=valid & result.mean_net_income.notna()
    return result

def attach_income(out,election_year,crosswalk=None):
    year=2022 if election_year==2022 else 2024
    meta_path=cache(API,f'scb/income/{SNAPSHOT}/metadata.json')
    meta=json.loads(meta_path.read_text())
    if meta['variables'][-1]['values'][-1]!=str(PRICE_YEAR):raise ValueError('Changed SCB price basis; audit and use a new snapshot')
    pattern=r'\d{4}[ABC]\d{4}' if election_year==2022 else r'\d{4}[ABC]\d{4}_DeSO2025'
    selection={'InkomstTyp':['NeInk'],'Kon':['1+2'],'ContentsCode':[MEAN,COUNT],'Tid':[str(year)]}
    query=[]
    for v in meta['variables']:
        values=[x for x in v['values'] if re.fullmatch(pattern,x)] if v['code']=='Region' else selection[v['code']]
        if not values or not set(values)<=set(v['values']):raise ValueError('Invalid income selection '+v['code'])
        query.append({'code':v['code'],'selection':{'filter':'item','values':values}})
    raw=cache(API,f'scb/income/{SNAPSHOT}/net_income_{year}.json',{'query':query,'response':{'format':'json-stat2'}})
    frame=jsonstat_frame(json.loads(raw.read_text())).pivot(index='Region',columns='ContentsCode',values='value').rename(columns={MEAN:'income_mean_tkr',COUNT:'income_persons'})
    frame.index=frame.index.str.replace('_DeSO2025','',regex=False);frame.index.name='deso_id';frame=frame.reset_index()
    cwpath=PROCESSED/f'crosswalk_{election_year}.parquet'
    cw=pd.read_parquet(cwpath) if crosswalk is None else crosswalk
    if set(cw.deso_id)!=set(frame.deso_id):raise ValueError('Income geography does not match crosswalk')
    values=estimate_income(frame,cw)
    if set(values.index)!=set(out.district_id):raise ValueError('Income district keys mismatch')
    result=out.drop(columns=[c for c in FIELDS if c in out]).merge(values,on='district_id',validate='one_to_one')
    result['income_year']=year;result['income_price_year']=PRICE_YEAR
    result['income_deso_year']=2018 if election_year==2022 else 2025
    result['income_grid_year']=2022 if election_year==2022 else 2025
    result['income_method']=np.where(result.income_complete,result.demography_method,'missing_source_cell')
    result['income_source_url']=SOURCE
    metadata=json.loads(raw.with_suffix('.json.metadata.json').read_text())
    provenance={'source_url':SOURCE,'api_url':API,'table':'Tab1InkDesoRegso','income_type':'NeInk','contents':{'mean_tkr':MEAN,'persons':COUNT},'raw_sha256':metadata['sha256'],'downloaded_at':metadata['downloaded_at'],'reference_year':year,'price_year':PRICE_YEAR,'unit':'SEK per person per year, constant 2024 prices','population':'Persons aged 20+ registered in Sweden throughout the reference year, according to SCB full-year-population restrictions; not all residents or eligible voters. Households with zero disposable income are excluded by the source.','definition':'Net income: taxable and tax-free personal income, including capital income and transfers, minus tax and other negative transfers such as student-loan repayments. Not salary, gross income, household-equivalised income or median income.','election_geometry_year':election_year,'deso_geometry_year':int(result.income_deso_year.iloc[0]),'population_grid_year':int(result.income_grid_year.iloc[0]),'deso_count':len(frame),'district_count':len(result),'complete_district_count':int(result.income_complete.sum()),'missing_source_deso_count':int(frame[['income_mean_tkr','income_persons']].isna().any(axis=1).sum()),'crosswalk_sha256':hashlib.sha256(cwpath.read_bytes()).hexdigest(),'method':'sum(w * source_persons * source_mean_tkr * 1000) / sum(w * source_persons). Same population-grid overlay as the atlas. No weighted medians, municipal substitutes, renormalisation of spatial weights or zero-filling. Any missing positive-weight source contributor suppresses the district estimate.','limitations':['Within each DeSO the income population and net income are assumed to follow the all-age population grid. Different income groups may live in different parts of the same DeSO.','For 2026 the income year is 2024, DeSO geography and population weights are from 2025, and electoral boundaries from 2026. It is not 2026 income or an estimate of income growth.','Source means and counts are rounded/disclosure controlled; reconstructed sums are approximate. Existing spatial coverage diagnostics also apply.','SCB assigns some geographically unlocatable persons to central DeSO/RegSO areas in their municipality.','Values for 2022 and 2024 are both expressed in constant 2024 prices. No district income trend is inferred across changed electoral boundaries.']}
    write_json(PUBLIC/str(election_year)/'income_provenance.json',provenance)
    frame.to_csv(PROCESSED/f'deso_net_income_{year}.csv',index=False)
    print(f'Income {year}: {len(frame)} DeSO -> {len(result)} districts, {result.income_complete.sum()} complete; range {result.mean_net_income.min():,.0f}–{result.mean_net_income.max():,.0f} SEK/year',flush=True)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--year',type=int,choices=[2022,2026]);args=parser.parse_args()
    cache(SOURCE,f'scb/income/{SNAPSHOT}/table_definition.html')
    for year in [args.year] if args.year else [2022,2026]:
        folder=PUBLIC/str(year);path=folder/'districts.json.gz'
        original=json.loads(gzip.decompress(path.read_bytes()))
        # Keep every pre-existing non-income JSON value exactly as published.
        values=attach_income(pd.DataFrame(original),year).set_index('district_id')
        added=json.loads(values[FIELDS].round(6).to_json(orient='index',force_ascii=False))
        updated=[{**row,**added[row['district_id']]} for row in original]
        for old,new in zip(original,updated):
            assert {k:v for k,v in old.items() if k not in FIELDS}=={k:v for k,v in new.items() if k not in FIELDS}
        path.write_bytes(gzip.compress(json.dumps(updated,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode(),mtime=0))
        for target in [folder/f'joined_{year}.csv',PROCESSED/f'joined_{year}.csv']:
            pd.DataFrame(updated).to_csv(target,index=False,float_format='%.6f')
if __name__=='__main__':main()
