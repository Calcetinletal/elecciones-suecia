from common import *
import gzip
for code,ids in [('0180',['01803936']),('2085',['20850401'])]:
 a=json.loads(gzip.decompress((PUBLIC/f'history/district_archive/{code}.json.gz').read_bytes()))
 print('MUNICIPALITY',code)
 for y in ['2026','2022','2018','2014','2010','2006','2002']:
  rows=[r for r in a['editions'][y] if r['district_id'] in ids]
  print(y,[(r['district_id'],r['district_name'],r['valid_votes']) for r in rows])
  linked=[i for r in rows for i in a['links'].get(y,{}).get(r['district_id'],[])];print('Official predecessors',linked)
  if linked:ids=linked
 for y,r in a['birth'].items():
  for id in ['01803936','20850401']:
   if id in r:print('BIRTH',y,id,[(v['year'],v['population']) for v in r[id]])
# Audit every serialized observation, including protected gaps and source denominators.
observations=0
for p in (PUBLIC/'history/district_archive').glob('*.gz'):
 a=json.loads(gzip.decompress(p.read_bytes()))
 for records in a['birth'].values():
  for rows in records.values():
   for r in rows:
    observations+=1;n=r['population'];cells=r['counts'].values()
    if n is not None and (n<0 or any(v is None or v<0 or v>n+.0001 for v in cells)):raise ValueError((p,r))
 for rows in a['editions'].values():
  for r in rows:
   if abs(sum(r['vote_'+party] for party in PARTIES)-r['valid_votes'])>.0001:raise ValueError((p,r))
print('Audited annual observations',observations)
