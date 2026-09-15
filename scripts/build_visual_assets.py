"""Build decorative origin silhouettes and cache party emblems for the static UI."""
from common import *
from shapely.geometry import shape
from shapely.ops import unary_union
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
ASSETS=ROOT/'public/assets/parties';ASSETS.mkdir(parents=True,exist_ok=True)
FILES={'C':'C v1.svg','KD':'Christian Democrats Sweden logo 2017.svg','L':'L v1.svg','M':'M plain v2.svg','V':'Vänsterpartiet logo.svg'}

def main():
 session=requests.Session();session.headers['User-Agent']='SwedenAtlas/1.0 (https://github.com; educational static atlas)'
 def get(url,name):
  p=RAW/'design'/name;meta=p.with_suffix(p.suffix+'.metadata.json')
  if p.exists() and meta.exists():
   d=json.loads(meta.read_text())
   if d['url']!=url or d['sha256']!=hashlib.sha256(p.read_bytes()).hexdigest():raise ValueError('Asset cache mismatch')
  else:
   r=session.get(url,timeout=60);r.raise_for_status();p.write_bytes(r.content);write_json(meta,{'url':url,'sha256':hashlib.sha256(r.content).hexdigest(),'downloaded_at':datetime.now(timezone.utc).isoformat()})
  return p
 query=urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url|extmetadata','titles':'|'.join('File:'+f for f in FILES.values())})
 raw=get('https://commons.wikimedia.org/w/api.php?'+query,'party_emblems_metadata.json');pages={v['title']:v for v in json.loads(raw.read_text())['query']['pages'].values()};credits=[]
 for code,filename in FILES.items():
  info=pages['File:'+filename]['imageinfo'][0];meta=info['extmetadata'];url=info['url'].split('?')[0];p=get(url,code+'_emblem.svg');ET.fromstring(p.read_bytes());(ASSETS/(code+'.svg')).write_bytes(p.read_bytes());credits.append({'code':code,'source':info['descriptionurl'],'url':url,'license':meta['LicenseShortName']['value'],'author':meta.get('Artist',{}).get('value'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 official={'S':('https://www.socialdemokraterna.se/images/18.5b29f63d180b3590ddd18dd/1652967347281/favicon-96x96.png','png'),'MP':('https://www.mp.se/wp-content/themes/mp/assets/images/logo-mobile.svg','svg'),'SD':('https://www.sd.se/wp-content/uploads/2022/07/logo_sd_logo_blasippa.png','png')}
 for code,(url,extension) in official.items():
  p=get(url,code+'_emblem.'+extension)
  if extension=='svg':ET.fromstring(p.read_bytes())
  elif not p.read_bytes().startswith(b'\x89PNG'):raise ValueError('Invalid PNG')
  (ASSETS/(code+'.'+extension)).write_bytes(p.read_bytes());credits.append({'code':code,'source':url,'license':'Party-owned emblem; used for editorial identification. Not included in the project MIT license.','sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 raw=cache('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_110m_admin_0_countries.geojson','design/ne_110m_countries_v5.1.2.geojson')
 features=json.loads(raw.read_text())['features'];bycode={f['properties']['ISO_A2_EH']:shape(f['geometry']) for f in features if f['properties']['ISO_A2_EH']!='-99'}
 def path(geometry):
  polys=list(geometry.geoms) if geometry.geom_type=='MultiPolygon' else [geometry]
  polys=[p.simplify(.12,preserve_topology=True) for p in polys if p.area>geometry.area*.001]
  bounds=unary_union(polys).bounds;x0,y0,x1,y1=bounds;scale=min(90/(x1-x0),90/(y1-y0));dx=(100-(x1-x0)*scale)/2;dy=(100-(y1-y0)*scale)/2
  return ' '.join('M'+' L'.join(f'{(x-x0)*scale+dx:.1f},{(y1-y)*scale+dy:.1f}' for x,y in p.exterior.coords)+' Z' for p in polys)
 shapes={code:path(g) for code,g in bycode.items() if not g.is_empty and code!='AQ'}
 mapping=json.loads((PUBLIC/'history/provenance.json').read_text())['country_mapping'];continents={'REG_AFRICA':'002','REG_ASIA':'142','REG_EUROPE_EX_SE':'150','REG_AMERICAS':'019','REG_OCEANIA':'009'}
 for code,continent in continents.items():shapes[code]=path(unary_union([g for c,g in bycode.items() if c!='SE' and mapping.get(c,{}).get('continent')==continent]))
 shapes['WORLD']=path(unary_union([g for c,g in bycode.items() if c!='AQ']))
 shapes['REG_NON_EUROPE']=path(unary_union([g for c,g in bycode.items() if mapping.get(c,{}).get('continent') in ['002','142','019','009']]))
 write_json(ROOT/'src/assets/origin-shapes.json',shapes)
 write_json(ROOT/'public/assets/credits.json',{'party_emblems':credits,'silhouettes':{'source':'https://www.naturalearthdata.com/about/terms-of-use/','dataset':json.loads(raw.with_suffix('.geojson.metadata.json').read_text()),'license':'Public domain','transform':'Decorative silhouettes simplified and fitted to a square. Small islands may be omitted. No effect on statistics.'}})
 print('Built 8 party emblems and',len(shapes),'decorative geographic silhouettes.')
if __name__=='__main__':main()
