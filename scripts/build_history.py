"""Reproducible official municipal/national time series; no district backcasting.
Run after build_countries.py/build_parents.py and the audited 2026 snapshot.
SCB omission of age/sex requests the table's official aggregate, not a sample.
"""
from common import *
from download_demography import jsonstat_frame
from build_parents import GROUPS
from build_birth_regions import TableRows
import gzip, math, zipfile, pandas as pd
from concurrent.futures import ThreadPoolExecutor

BASE=SOURCES['api_base']; YEARS=[str(y) for y in range(2002,2025)]
SPECS={'votes':'ME/ME0104/ME0104C/ME0104T3','parents':'BE/BE0101/BE0101Q/UtlSvBakgFin','birth':'BE/BE0101/BE0101E/FolkmRegFlandK','national_birth':'BE/BE0101/BE0101E/FodelselandArK'}
PAGES={k:'https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__'+p.rsplit('/',1)[0].replace('/','__')+'/'+p.rsplit('/',1)[1]+'/' for k,p in SPECS.items()}

def readgz(p):return json.loads(gzip.decompress(p.read_bytes()))
def dumpgz(p,d):p.write_bytes(gzip.compress(json.dumps(d,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode(),mtime=0))
def clean(x):return int(x) if x is not None and pd.notna(x) and math.isfinite(float(x)) else None
def query(kind,filename,selection):
 payload={'query':[{'code':k,'selection':{'filter':'item','values':v}} for k,v in selection.items()],'response':{'format':'json-stat2'}}
 path=cache(BASE+SPECS[kind],'history/'+filename+'.json',payload)
 return jsonstat_frame(json.loads(path.read_text()))

def main():
 folder=PUBLIC/'history';folder.mkdir(exist_ok=True)
 current=readgz(PUBLIC/'countries/birth_2025.json.gz');parents=readgz(PUBLIC/'parents/background_2025.json.gz')
 metas={k:json.loads(cache(BASE+p,'history/'+k+'_series_metadata.json').read_text()) for k,p in SPECS.items()}
 values=lambda kind,code:next(v['values'] for v in metas[kind]['variables'] if v['code']==code)
 regions={r['code']:{'code':r['code'],'name':'Suecia' if r['code']=='00' else r['name'],'level':r['level']} for r in parents['regions'] if r['level']!='county'}
 out={c:{'code':c,'votes':[],'parents':[],'birth':[]} for c in regions}
 tasks=[('votes','votes_2002_2022',{'Region':values('votes','Region'),'Partimm':['S','M','SD','V','C','KD','FP','MP','ÖVRIGA'],'ContentsCode':['ME0104B6','ME0104B7'],'Tid':[str(y) for y in range(2002,2023,4)]}),('parents','parents_2002_2024',{'Region':list(regions),'UtlBakgrund':list(GROUPS),'Tid':YEARS}),('parents','population_2002_2024',{'Region':list(regions),'Tid':YEARS}),('national_birth','national_birth_2002_2024',{'Fodelseland':values('national_birth','Fodelseland'),'Tid':YEARS})]
 for i in range(0,len(YEARS),2):tasks.append(('birth','birth_'+YEARS[i]+'_'+YEARS[min(i+1,len(YEARS)-1)],{'Region':[c for c in regions if c!='00' and c in values('birth','Region')],'Fodelseregion':values('birth','Fodelseregion'),'Kon':['1+2'],'Tid':YEARS[i:i+2]}))
 with ThreadPoolExecutor(max_workers=3) as pool:frames=list(pool.map(lambda t:query(*t),tasks))
 votes,pf,totals,national=frames[:4]
 pop={(str(r.Region),int(r.Tid)):clean(r.value) for r in totals.itertuples()}
 for (code,year),frame in pf.groupby(['Region','Tid']):
  counts={GROUPS[r.UtlBakgrund][0]:clean(r.value) for r in frame.itertuples()};n=pop.get((code,int(year)))
  if n and all(x is not None for x in counts.values()) and sum(counts.values())!=n:raise ValueError('Parent partition mismatch '+code+year)
  out[code]['parents'].append({'year':int(year),'population':n,'counts':counts})
 for r in parents['regions']:
  if r['code'] in out:out[r['code']]['parents'].append({'year':2025,'population':r['population'],'counts':r['counts'],'ckm':True})
 mapping={'FP':'L','ÖVRIGA':'other'}
 for (code,year),frame in votes.groupby(['Region','Tid']):
  code='00' if code=='VR00' else code
  if code not in out:continue
  pivot=frame.pivot(index='Partimm',columns='ContentsCode',values='value')
  counts={mapping.get(k,k):clean(row['ME0104B6']) for k,row in pivot.iterrows()}
  # A missing municipality-year remains missing; it is never zero-filled.
  total=sum(counts.values()) if all(n is not None for n in counts.values()) else None
  pct={k:100*n/total if total and n is not None else None for k,n in counts.items()}
  for k,row in pivot.iterrows():
   calculated=pct[mapping.get(k,k)];published=row['ME0104B7']
   if calculated is not None and pd.notna(published) and abs(calculated-published)>.11:raise ValueError('Election percentage mismatch '+code+year+k)
  out[code]['votes'].append({'year':int(year),'total':total,'counts':counts,'pct':pct,'status':'definitive'})
 # Include all reporting units; unreported collection units remain pending.
 manifest=json.loads((PUBLIC/'manifest.json').read_text());entry=next(y for y in manifest['years'] if y['year']==2026)
 snapshot=entry['snapshot']
 zip_path=RAW/'val2026'/snapshot/'results.zip'
 if not zip_path.exists():raise ValueError('Missing audited 2026 snapshot '+str(zip_path))
 if not entry.get('signatures_verified') or hashlib.sha256(zip_path.read_bytes()).hexdigest()!=entry['election_sha256']:raise ValueError('2026 source differs from the audited, signed snapshot')
 with zipfile.ZipFile(zip_path) as z:raw=json.loads(z.read(next(n for n in z.namelist() if 'rostfordelning' in n and n.endswith('.json'))))
 parties=[p['id'] for p in json.loads((ROOT/'config/parties.json').read_text())]
 accum={c:{'year':2026,'total':0,'counts':{p:0 for p in parties},'status':'provisional','reported_units':0,'expected_units':0} for c in out}
 for r in raw['valdistrikt']:
  for code in ['00',r['kommunkod']]:
   if code not in accum:raise ValueError('Unknown municipality '+code)
   rec=accum[code];rec['expected_units']+=1
   if not r.get('rostfordelning'):continue
   rec['reported_units']+=1;v=r['rostfordelning']['rosterPaverkaMandat'];rec['total']+=v['antalRoster']
   for p in v['partiRoster']:rec['counts'][p['partiforkortning']]+=p['antalRoster']
   rec['counts']['other']+=v['rosterOvrigaPartier']['antalRoster']
 for code,rec in accum.items():
  if sum(rec['counts'].values())!=rec['total']:raise ValueError('2026 valid vote sum mismatch')
  rec['pct']={k:100*n/rec['total'] if rec['total'] else None for k,n in rec['counts'].items()};out[code]['votes'].append(rec)
 # Geographic definitions follow the existing M49 mapping for all years.
 info=json.loads((PUBLIC/'countries/birth_regions_definition.json').read_text());country_mapping=info['country_mapping']
 parser=TableRows();parser.feed((RAW/'scb/countries/un_m49_overview.html').read_text())
 un={r[10]:{'continent':r[2],'subregion':r[4]} for r in parser.rows if len(r)==15 and r[1]=='World' and r[10]}
 countries={c['code']:c for c in current['countries']}
 for kind,dim in [('birth','Fodelseregion'),('national_birth','Fodelseland')]:
  variable=next(v for v in metas[kind]['variables'] if v['code']==dim)
  for code,name in zip(variable['values'],variable['valueTexts']):
   if code=='TOTfod':continue
   countries.setdefault(code,{'code':code,'name_sv':name,'kind':'country'})
   if code not in country_mapping:country_mapping[code]=un.get(code,{'continent':'unassigned','subregion':'unassigned','method':'No verified M49 assignment'})
 continent_ids={'REG_AFRICA':'002','REG_ASIA':'142','REG_EUROPE_EX_SE':'150','REG_AMERICAS':'019','REG_OCEANIA':'009','REG_UNASSIGNED':'unassigned'}
 groups=[]
 for g in current['birth_groups']:
  if g['code'] not in continent_ids and g['code']!='REG_NON_EUROPE':continue
  g={**g,'members':[c for c in countries if c!='SE' and (country_mapping[c]['continent'] in ['002','142','019','009'] if g['code']=='REG_NON_EUROPE' else country_mapping[c]['continent']==continent_ids[g['code']])]};groups.append(g)
 def add_birth(code,year,counts,total,ckm=False):
  # SCB pools small country counts; zero outside Sweden is ambiguous in both tables.
  counts={k:(None if v==0 and k not in ['SE','ÖOF','OVFOD'] else v) for k,v in counts.items()}
  missing={}
  for g in groups:
   available=[counts.get(c) for c in g['members'] if counts.get(c) is not None]
   missing[g['code']]=len(g['members'])-len(available)
   counts[g['code']]=sum(available) if available else None
  out[code]['birth'].append({'year':year,'population':total,'counts':counts,'missing':missing,'ckm':ckm})
 for frame in frames[4:]:
  for (code,year),group in frame.groupby(['Region','Tid']):
   counts={r.Fodelseregion:clean(r.value) for r in group.itertuples()};total=counts.pop('TOTfod',None)
   add_birth(code,int(year),counts,total)
 for year,frame in national.groupby('Tid'):
  add_birth('00',int(year),{r.Fodelseland:clean(r.value) for r in frame.itertuples()},pop.get(('00',int(year))))
 for r in current['regions']:
  if r['code'] in out:add_birth(r['code'],2025,{c['code']:r['counts'].get(c['code']) for c in current['countries']},r['population'],True)
 # Breaks: SCB birth/population geography is 1 January following reference year.
 # SCB explicitly already reports Knivsta separately in the 2002 election.
 # Heby's county/code changed, not its municipal extent; SCB supplies its series.
 breaks={'0186':{'parents':[2010],'birth':[2010],'votes':[2011]},'0187':{'parents':[2010],'birth':[2010],'votes':[2011]}}
 for code,data in out.items():
  data['breaks']=breaks.get(code,{})
  for measure in ['votes','parents','birth']:
   data[measure].sort(key=lambda r:r['year'])
   expected=7 if measure=='votes' else 24
   if len(data[measure])!=expected:raise ValueError('Unexpected series length '+code+measure+str(len(data[measure])))
   for row in data[measure]:
    denom=row.get('population',row.get('total'))
    if denom is not None and denom<0:raise ValueError('Negative denominator')
    if any(v is not None and (v<0 or denom is not None and v>denom) for v in row['counts'].values()):raise ValueError('Count outside denominator '+code+measure+str(row['year']))
  dumpgz(folder/(code+'.json.gz'),data)
 sources={**PAGES,'parents_2025':parents['source_url'],'birth_2025':current['source_url']}
 provenance={'sources':sources,'inputs_2025':[{**json.loads((PUBLIC/p).read_text()),'published_file':f,'published_sha256':hashlib.sha256((PUBLIC/f).read_bytes()).hexdigest()} for p,f in [('parents/provenance.json','parents/background_2025.json.gz'),('countries/provenance.json','countries/birth_2025.json.gz')]],'source_2026':'https://resultat.val.se/resultatfiler/val2026/p/rd/Val_2026_preliminar_00_RD.zip','source_updated_2026':raw['senasteUppdateringstid'],'sha256_2026':hashlib.sha256(zip_path.read_bytes()).hexdigest(),'snapshot_2026':snapshot,'notes':['Election denominator: valid votes, counts summed before division. FP continues as L. Other includes all other valid parties.','2026 provisional: all reporting units included when reported; pending collection units are not final zeros.','Parents: official SCB aggregates across ages and sexes, four disjoint groups, separate official population denominator. 2025 CKM may alter additivity.','Birth country: SCB small-country pooling retained; non-Sweden zeros treated as ambiguous. Continental series are published-cell subtotals, not exhaustive totals.','Birthplace is not ethnicity or religion and these series do not measure voting by origin.','Municipal observations retain each year geography. No historical observations are assigned to present-day electoral districts. Flagged boundary changes break lines. Country recognition/coding can change over time.','Population is observed 31 December; 2025 is latest available. No 2026 population estimate is invented.'],'country_mapping':country_mapping,'raw_files':[json.loads(p.read_text()) for p in sorted((RAW/'history').glob('*.metadata.json'))]}
 write_json(folder/'provenance.json',provenance)
 write_json(folder/'index.json',{'regions':list(regions.values()),'parents':parents['countries'],'countries':list(countries.values()),'groups':groups,'source_updated_2026':raw['senasteUppdateringstid'],'sources':sources})
 print('History: validated',len(out),'territories; votes 2002–2026, population 2002–2025.',flush=True)
if __name__=='__main__':main()
