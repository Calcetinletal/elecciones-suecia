"""Build municipal display outlines from each election's own official district geometry."""
import gzip
import hashlib
import json
from pathlib import Path
from shapely.geometry import shape, mapping
from shapely.ops import unary_union, transform
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'public/data'
forward = Transformer.from_crs(4326, 3006, always_xy=True).transform
back = Transformer.from_crs(3006, 4326, always_xy=True).transform
manifest = json.loads((DATA / 'manifest.json').read_text())
for entry in manifest['years']:
    if not entry.get('table') or not entry.get('geometry'):
        continue
    rows = json.loads(gzip.decompress((DATA / entry['table']).read_bytes()))
    lookup = {d['district_id']: d['municipality_code'] for d in rows}
    source = DATA / entry['geometry']
    geometry = json.loads(gzip.decompress(source.read_bytes()))
    groups = {}
    for feature in geometry['features']:
        code = lookup[feature['properties']['district_id']]
        groups.setdefault(code, []).append(shape(feature['geometry']))
    features = []
    for code, polygons in sorted(groups.items()):
        merged = unary_union(polygons)
        simplified = transform(back, transform(forward, merged).simplify(50, preserve_topology=True))
        features.append({'type': 'Feature', 'properties': {'district_id': code, 'municipality_code': code}, 'geometry': mapping(simplified)})
    result = {'type': 'FeatureCollection', 'features': features, 'provenance': {'source': entry['geometry'], 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'year': entry['year'], 'method': 'Union of the same election-year Valmyndigheten districts by municipality; display simplification 50 m in SWEREF 99 TM. Vote counts are unchanged.'}}
    target = DATA / str(entry['year']) / 'municipalities.geojson.gz'
    target.write_bytes(gzip.compress(json.dumps(result, separators=(',', ':')).encode(), mtime=0))
    print(f'{entry["year"]}: {len(features)} municipalities; {target.stat().st_size:,} bytes', flush=True)
