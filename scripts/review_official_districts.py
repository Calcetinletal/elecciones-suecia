import sys,json
sys.path.insert(0,'scripts')
from common import cache
url='https://services8.arcgis.com/9CUL84k8apjo6IDh/arcgis/rest/services/Valdistrikt_SocEk_ValResult_2022/FeatureServer/0'
p=cache(url+'?f=pjson','audit/district_official_review_20260914_layer.json')
d=json.loads(p.read_text());print('DESCRIPTION',d.get('description'));print('COPYRIGHT',d.get('copyrightText'));print('FIELDS',[(f['name'],f.get('alias')) for f in d['fields']])
q=url+'/query?where=1%3D1&outFields=*&returnGeometry=false&resultRecordCount=1&f=json'
p=cache(q,'audit/district_official_review_20260914_sample.json');d=json.loads(p.read_text());print('SAMPLE',d)
