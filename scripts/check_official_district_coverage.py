import sys,json,gzip,urllib.parse
sys.path.insert(0,'scripts')
from common import cache,write_json,ROOT
url='https://services8.arcgis.com/9CUL84k8apjo6IDh/arcgis/rest/services/Valdistrikt_SocEk_ValResult_2022/FeatureServer/0/query'
params={'where':'1=1','outFields':'Valdistrik,Valdistr_1,Fo_Utrikes,FO_TOTföd,Röstberättigade','returnGeometry':'false','orderByFields':'OBJECTID_1','resultRecordCount':2000,'f':'json'}
rows=[]
for offset in range(0,10000,2000):
 params['resultOffset']=offset
 path=cache(url+'?'+urllib.parse.urlencode(params),f'audit/district_official_review_20260914_rows_{offset}.json')
 data=json.loads(path.read_text());rows += [f['attributes'] for f in data.get('features',[])]
 if not data.get('exceededTransferLimit'):break
existing=json.loads(gzip.decompress((ROOT/'public/data/2022/districts.json.gz').read_bytes()))
old={r['district_id']:r for r in existing};ids={r['Valdistrik'] for r in rows}
checks={'rows':len(rows),'unique_ids':len(ids),'matches_current_atlas':len(ids&set(old)),'missing_from_direct_layer':sorted(set(old)-ids),'extra_direct_layer':sorted(ids-set(old)),'missing_birth_cells':sum(r['Fo_Utrikes'] is None or r['FO_TOTföd'] is None for r in rows),'invalid_birth_counts':sum(r['Fo_Utrikes'] is not None and r['FO_TOTföd'] is not None and not 0<=r['Fo_Utrikes']<=r['FO_TOTföd'] for r in rows),'denominator_differs_electoral_eligible':sum(r['FO_TOTföd']!=r['Röstberättigade'] for r in rows),'sample':rows[0]}
write_json(ROOT/'data/raw/audit/district_official_review_checks.json',checks)
print(json.dumps(checks,ensure_ascii=False,indent=2))
