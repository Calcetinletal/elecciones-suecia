"""Download official SCB tables by historical DeSO, not district HTML."""
from common import *
import re, itertools
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

DEFINITIONS={
 'background': {'year':'2022','dimension':'UtlBakgrund','values':['1','SA']},
 'birth': {'year':'2022','dimension':'Fodelseregion','values':['sv','tot']},
 'citizenship': {'year':'2022','dimension':'Medborgarskap','values':['sv','SA']},
 'education': {'year':'2022','dimension':'UtbildningsNiva','values':['21','3+4','5','6','US']},
 'employment': {'year':'2021','dimension':'Sysselsattning','values':['FÖRV','total']},
}

def jsonstat_frame(d):
    dims=d['id']; categories=[]
    for dim in dims:
        ix=d['dimension'][dim]['category']['index']
        categories.append(ix if isinstance(ix,list) else sorted(ix,key=ix.get))
    values=d['value']
    if isinstance(values,dict): values=[values.get(str(i)) for i in range(__import__('math').prod(d['size']))]
    return pd.DataFrame([dict(zip(dims,key),value=value) for key,value in zip(itertools.product(*categories),values)])

def download_table(name):
    spec=DEFINITIONS[name]; url=SOURCES['api_base']+SOURCES['tables'][name]
    meta=json.loads(cache(url,f'scb/{name}_metadata.json').read_text())
    query=[]
    for v in meta['variables']:
        code=v['code']
        selected=[x for x in v['values'] if re.fullmatch(r'\d{4}[ABC]\d{4}',x)] if code=='Region' else [spec['year']] if code=='Tid' else ['1+2'] if code=='Kon' else spec['values'] if code==spec['dimension'] else v['values']
        if not set(selected)<=set(v['values']): raise ValueError(f'Missing codes {name}/{code}')
        query.append({'code':code,'selection':{'filter':'item','values':selected}})
    payload={'query':query,'response':{'format':'json-stat2'}}
    raw=cache(url,f'scb/{name}_{spec["year"]}.json',payload)
    frame=jsonstat_frame(json.loads(raw.read_text())).pivot(index='Region',columns=spec['dimension'],values='value')
    frame.index.name='deso_id'
    return name,frame

def main():
    with ThreadPoolExecutor(max_workers=3) as pool: frames=dict(pool.map(download_table,DEFINITIONS))
    b=frames['background']; out=pd.DataFrame(index=b.index)
    out['population']=b['SA'];out['foreign_background_count']=b['1']
    out['birth_population']=frames['birth']['tot'];out['foreign_born_count']=frames['birth']['tot']-frames['birth']['sv']
    out['citizenship_population']=frames['citizenship']['SA'];out['foreign_citizens_count']=frames['citizenship']['SA']-frames['citizenship']['sv']
    out['education_population']=frames['education'].sum(axis=1,min_count=5)
    out['higher_education_count']=frames['education'][['5','6']].sum(axis=1,min_count=2)
    out['employment_population']=frames['employment']['total'];out['employed_count']=frames['employment']['FÖRV']
    out.to_csv(PROCESSED/'deso_demography.csv')
    for key in ['deso_2018','grid_2022']: cache(SOURCES[key],f'scb/{key}.gpkg')
    print('Demography:',len(out),'DeSO; null values',out.isna().sum().to_dict(),flush=True)
if __name__=='__main__': main()
