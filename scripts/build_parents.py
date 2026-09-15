"""Publish SCB's detailed parental birthplace groups at their observed municipal scale."""
from common import *
from download_demography import jsonstat_frame
import gzip, math
API=SOURCES['api_base']+'BE/BE0101/BE0101Q/UtlSvBakgFinCKM'
SOURCE='https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__BE__BE0101__BE0101Q/UtlSvBakgFinCKM/'
GROUPS={
 '08':('PARENT_FOREIGN_BORN','Nacidos fuera de Suecia','Personas nacidas fuera de Suecia, con independencia de dónde nacieron sus progenitores.'),
 '4':('PARENT_BOTH_FOREIGN','Nacidos en Suecia · ambos padres fuera','Nacidos en Suecia con los dos progenitores nacidos en el extranjero.'),
 '5':('PARENT_MIXED','Nacidos en Suecia · un padre fuera','Nacidos en Suecia con un progenitor nacido en Suecia y otro en el extranjero. SCB incluye este grupo en «origen sueco».'),
 '6':('PARENT_BOTH_SWEDEN','Nacidos en Suecia · ambos padres en Suecia','Nacidos en Suecia con los dos progenitores nacidos en Suecia.'),
}
def build_data(raw,meta,provenance):
 frame=jsonstat_frame(raw).pivot(index='Region',columns='UtlBakgrund',values='value')
 variable=next(v for v in meta['variables'] if v['code']=='Region');names=dict(zip(variable['values'],variable['valueTexts']))
 dimension=next(v for v in meta['variables'] if v['code']=='UtlBakgrund');labels=dict(zip(dimension['values'],dimension['valueTexts']))
 categories=[{'code':code,'kind':'parent','name_es':name,'name_sv':labels[k],'description':desc,'source_code':k} for k,(code,name,desc) in GROUPS.items()]
 def cell(x):return None if x is None or not math.isfinite(float(x)) else int(x)
 regions=[]
 for code,row in frame.iterrows():
  total=cell(row['TotUI']);counts={name:cell(row[k]) for k,(name,_,_) in GROUPS.items()}
  if total is None or total<=0:raise ValueError('Missing population '+code)
  if any(n is not None and (n<0 or n>total) for n in counts.values()):raise ValueError('Invalid source count '+code)
  regions.append({'code':code,'name':names[code],'level':'national' if code=='00' else 'county' if len(code)==2 else 'municipality','population':total,'counts':counts,'component_sum_gap':None if any(n is None for n in counts.values()) else sum(counts.values())-total})
 return {'year':2025,'reference_date':'2025-12-31','source_url':SOURCE,'downloaded_at':provenance['downloaded_at'],'countries':categories,'regions':regions,'definition':'Birthplace of the person and parents, not citizenship, ethnicity or religion. Percentages use the independently published total from this same table. SCB disclosure control may prevent components summing to total. Municipal observations are not assigned to electoral districts.'}
def main():
 meta=json.loads(cache(API,'scb/parents/municipal_metadata.json').read_text());query=[]
 for v in meta['variables']:
  code=v['code'];values=['TotUI',*GROUPS] if code=='UtlBakgrund' else ['tot'] if code=='Alder' else ['TotSa'] if code=='Kon' else ['2025'] if code=='Tid' else v['values']
  if not set(values)<=set(v['values']):raise ValueError('Invalid selection '+code)
  query.append({'code':code,'selection':{'filter':'item','values':values}})
 path=cache(API,'scb/parents/parental_background_2025.json',{'query':query,'response':{'format':'json-stat2'}})
 provenance=json.loads(path.with_suffix('.json.metadata.json').read_text());result=build_data(json.loads(path.read_text()),meta,provenance)
 if sum(r['level']=='municipality' for r in result['regions'])!=290:raise ValueError('Expected 290 municipalities')
 existing=json.loads(gzip.decompress((PUBLIC/'countries/birth_2025.json.gz').read_bytes()))
 if {r['code'] for r in result['regions']}!={r['code'] for r in existing['regions']}:raise ValueError('Region keys differ')
 folder=PUBLIC/'parents';folder.mkdir(exist_ok=True)
 (folder/'background_2025.json.gz').write_bytes(gzip.compress(json.dumps(result,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode(),mtime=0))
 import pandas as pd
 records=[{'region_code':r['code'],'region_name':r['name'],'level':r['level'],'category_code':c['code'],'category_name':c['name_es'],'source_category_code':c['source_code'],'published_count':r['counts'][c['code']],'population_denominator':r['population'],'pct_all_residents':None if r['counts'][c['code']] is None else 100*r['counts'][c['code']]/r['population'],'reference_date':result['reference_date'],'source_url':SOURCE} for r in result['regions'] for c in result['countries']]
 pd.DataFrame(records).to_csv(folder/'background_2025.csv',index=False,float_format='%.6f')
 write_json(folder/'provenance.json',{**provenance,'table_page':SOURCE,'definition':result['definition'],'groups':result['countries'],'region_count':len(result['regions']),'observations':len(records),'municipalities':290,'max_abs_component_sum_gap':max(abs(r['component_sum_gap'] or 0) for r in result['regions'])})
 print('Parents:',len(records),'published cells; national:',next(r for r in result['regions'] if r['code']=='00'),flush=True)
if __name__=='__main__':main()
