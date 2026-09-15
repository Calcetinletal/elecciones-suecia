"""Download SCB 2025 birth-country counts at their published municipal level."""
from common import *
from download_demography import jsonstat_frame
import pandas as pd
import geopandas as gpd
import gzip, subprocess
URL=SOURCES['api_base']+'BE/BE0101/BE0101E/FolkmRegFlandKCKM'
PAGE='https://www.statistikdatabasen.scb.se/pxweb/en/ssd/START__BE__BE0101__BE0101E/FolkmRegFlandKCKM/'

def main():
    meta=json.loads(cache(URL,'scb/countries/FolkmRegFlandKCKM_metadata.json').read_text())
    query=[]
    for v in meta['variables']:
        selected=['TotSa'] if v['code']=='Kon' else ['2025'] if v['code']=='Tid' else v['values']
        query.append({'code':v['code'],'selection':{'filter':'item','values':selected}})
    path=cache(URL,'scb/countries/birth_countries_2025.json',{'query':query,'response':{'format':'json-stat2'}})
    raw=json.loads(path.read_text());df=jsonstat_frame(raw)
    if df.duplicated(['Region','Fodelseregion']).any():raise ValueError('Duplicate country/region')
    totals=df[df.Fodelseregion=='TOTfod'].set_index('Region').value
    if (df.value.dropna()<0).any() or (totals<=0).any():raise ValueError('Invalid counts')
    labels={v['code']:dict(zip(v['values'],v['valueTexts'])) for v in meta['variables']}
    countries=[{'code':code,'name_sv':name,'kind':'group' if code in ['ÖOF','OVFOD'] else 'country'} for code,name in labels['Fodelseregion'].items() if code!='TOTfod']
    regions=[];csv=[]
    for code,group in df.groupby('Region',sort=True):
        counts=dict(zip(group.Fodelseregion,group.value));population=counts.pop('TOTfod')
        regions.append({'code':code,'name':labels['Region'][code],'level':'national' if code=='00' else 'county' if len(code)==2 else 'municipality','population':int(population),'counts':{k:None if pd.isna(v) else int(v) for k,v in counts.items()}})
        for country,n in counts.items():
            ambiguous=country not in ['SE','ÖOF','OVFOD'] and n==0
            status='missing' if pd.isna(n) else 'zero_or_grouped' if ambiguous else 'published'
            csv.append({'region_code':code,'region_name':labels['Region'][code],'country_code':country,'country_name_sv':labels['Fodelseregion'][country],'year':2025,'reference_date':'2025-12-31','published_count':n,'population_denominator':population,'pct_all_residents':100*n/population if status=='published' else None,'status':status,'geographic_level':regions[-1]['level'],'source_url':PAGE})
    table=pd.DataFrame(csv)
    if not table.pct_all_residents.dropna().between(0,100).all():raise ValueError('Invalid percentages')
    municipalities={r['code'] for r in regions if r['level']=='municipality'}
    # Use the already validated electoral outlines solely to draw municipalities.
    # No municipal country count is allocated to a valdistrikt.
    outlines=gpd.read_parquet(PROCESSED/'boundaries_2026.parquet')[['municipality_code','geometry']].dissolve('municipality_code',as_index=False)
    if set(outlines.municipality_code)!=municipalities:raise ValueError('Municipal geometry/table mismatch')
    source=PROCESSED/'country_municipalities_input.geojson';outlines.to_file(source,driver='GeoJSON')
    output=PROCESSED/'country_municipalities_simplified.geojson'
    subprocess.run(['node',str(ROOT/'node_modules/mapshaper/bin/mapshaper'),str(source),'-snap','interval=0.01','-clean','gap-fill-area=0','-simplify','weighted','interval=50','keep-shapes','-proj','from=EPSG:3006','EPSG:4326','-o',str(output),'precision=0.000001','format=geojson','force'],check=True)
    geo=gpd.read_file(output);geo.geometry=geo.geometry.make_valid().set_precision(.000001)
    if not geo.is_valid.all() or geo.is_empty.any() or set(geo.municipality_code)!=municipalities:raise ValueError('Invalid web municipality geometry')
    payload=json.loads(geo.to_json(drop_id=True))
    for f in payload['features']:f['id']=f['properties']['municipality_code']
    folder=PUBLIC/'countries';folder.mkdir(exist_ok=True)
    download=json.loads(path.with_suffix('.json.metadata.json').read_text())
    provenance={'reference_date':'2025-12-31','year':2025,'downloaded_at':download['downloaded_at'],'source_url':PAGE,'source_api':URL,'sha256':download['sha256'],'license':'SCB CC0; map outlines Valmyndigheten with attribution','country_categories':len(countries),'municipalities':len(municipalities),'geography':'Municipal display outlines dissolved from Valmyndigheten 2026 districts, simplified 50m; statistics are published by SCB at municipality/county/national level','disclosure_control':'CKM; groups smaller than 10 regionally / 20 nationally are grouped as other countries. A zero individual-country cell may mean zero or grouped; no exact zero percentage is inferred. Independent cell protection means sums may differ from totals.'}
    data={**provenance,'countries':countries,'regions':regions}
    (folder/'birth_2025.json.gz').write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode(),mtime=0))
    (folder/'municipalities.geojson.gz').write_bytes(gzip.compress(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
    table.to_csv(folder/'birth_2025.csv',index=False,float_format='%.6f')
    write_json(folder/'provenance.json',provenance)
    print(json.dumps(provenance,ensure_ascii=False,indent=2));print('Missing counts:',int(table.published_count.isna().sum()),'Zero or grouped:',int(table.status.eq('zero_or_grouped').sum()))
    from build_birth_regions import main as build_regions
    build_regions()
    from build_parents import main as build_parent_groups
    build_parent_groups()
if __name__=='__main__':main()
