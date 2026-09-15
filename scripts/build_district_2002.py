"""Import the complete official 2002 district HTML archive, with immutable source caching."""
from common import *
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse
from concurrent.futures import ThreadPoolExecutor
import re,gzip
START='https://historik.val.se/val/val_02/slutresultat/00R/00.html'
PATTERN=re.compile(r'https://historik.val.se/val/val_02/slutresultat/\d{2}R/(?:\d{4}/)?(?:\d{2}|\d{4}|\d{6}|\d{8}|\d{4}KR|R-\d{4}-\d{2})\.html$')
def load(url):
 path=cache(url,'history_full/2002/'+url.split('/slutresultat/')[1])
 html=path.read_text(encoding='utf-8');soup=BeautifulSoup(html,'html.parser')
 links={urljoin(url,a['href']).split('#')[0] for a in soup.find_all('a',href=True)}
 links={u for u in links if PATTERN.fullmatch(u)}
 stem=Path(urlparse(url).path).stem
 row=None
 if re.fullmatch(r'\d{8}|R-\d{4}-\d{2}',stem):
  title=soup.title.get_text(' ',strip=True)
  for tr in soup.find_all('tr'):
   header=[t.get_text(' ',strip=True) for t in tr.find_all('th',recursive=False)];header=[t for t in header if t]
   if all(p in header for p in ['M','C','FP','KD','S','V','MP']):
    data=tr.find_next_sibling('tr');columns=tr.find_all('th',recursive=False);cells=data.find_all('td',recursive=False)
    positions=[(i,c.get_text(' ',strip=True)) for i,c in enumerate(columns) if c.get_text(' ',strip=True)]
    if len(columns)!=len(cells):raise ValueError(('Header/count layout mismatch',url,len(columns),len(cells)))
    counts={key:int(cells[i].get_text(' ',strip=True).replace('\xa0','') or '0') for i,key in positions};break
  else:raise ValueError('Vote table missing '+url)
  valid=sum(v for k,v in counts.items() if k not in ['OG','BLANK'])
  sd=counts.get('SD')
  if sd is None:
   # Other-party details use SD's official party abbreviation, not its position.
   for tr in soup.find_all('tr'):
    cells=[c.get_text(' ',strip=True) for c in tr.find_all('td',recursive=False) if c.get_text(' ',strip=True)]
    if len(cells)==3 and cells[0]=='SD':sd=int(cells[2]);break
   if sd is None:sd=0 # Complete list of other parties omits zero-vote parties.
  values={p:counts['FP' if p=='L' else p] for p in PARTIES[:-1] if p!='SD'};values['SD']=sd
  values['other']=valid-sum(values.values())
  if valid<=0 or min(values.values())<0:raise ValueError('Invalid vote partition '+url)
  row={'district_id':stem,'district_name':title.split(' - ')[0].strip(),'municipality_code':stem.split('-')[1] if stem.startswith('R-') else stem[:4],'election_year':2002,'election_status':'definitive','valid_votes':valid,'election_source_url':url,**{'vote_'+k:v for k,v in values.items()}}
 return url,links,row

def main():
 seen=set();queue={START};rows=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  while queue:
   batch=sorted(queue-seen);queue=set();seen.update(batch)
   for url,links,row in pool.map(load,batch):
    queue.update(links-seen)
    if row:rows.append(row)
   print('2002 progress',len(seen),'pages,',len(rows),'district records',flush=True)
 if len({r['district_id'] for r in rows})!=len(rows):raise ValueError('Duplicate district IDs')
 # Collection units have codes ending 0000 and are not physical districts.
 physical=[r for r in rows if not r['district_id'].startswith('R-') and not r['district_id'].endswith('0000') and 'ej räknade' not in r['district_name'].lower()]
 if len(rows)!=6266:raise ValueError(f'Expected published 6266 reporting units, got {len(rows)}')
 # National valid-party counts independently checked against the archive's national table.
 national={p:sum(r['vote_'+p] for r in rows) for p in PARTIES}
 expected={'M':809041,'C':328428,'L':710312,'KD':485235,'S':2113560,'V':444854,'MP':246392,'SD':76300}
 if any(national[p]!=n for p,n in expected.items()):raise ValueError(('National totals disagree',national))
 payload=json.dumps({'rows':physical,'previous':{},'year':2002,'source':START},ensure_ascii=False,separators=(',',':')).encode()
 (PUBLIC/'history/districts_2002.json.gz').write_bytes(gzip.compress(payload,mtime=0))
 write_json(PUBLIC/'history/districts_2002_provenance.json',{'source':START,'pages':len(seen),'reporting_units':len(rows),'physical_districts':len(physical),'national_validation':national,'method':'Individual district HTML result tables. SD extracted from the full other-party detail and subtracted from other. Collection units excluded. No historical geography inferred from a reused code. Original HTML and SHA256 sidecars cached.'})
 print('2002 complete',len(physical),national,flush=True)
if __name__=='__main__':main()
