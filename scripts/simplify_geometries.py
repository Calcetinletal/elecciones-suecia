"""Offline shared-boundary simplification with mapshaper; retain analysis geometry."""
from common import *
import geopandas as gpd
import subprocess,gzip,shutil

def main(year=2022):
    original=gpd.read_parquet(PROCESSED/f'boundaries_{year}.parquet')
    source=PROCESSED/f'web_input_{year}.geojson'
    original[['district_id','geometry']].to_file(source,driver='GeoJSON')
    cli=ROOT/'node_modules/mapshaper/bin/mapshaper'
    if not cli.exists(): raise RuntimeError('Run npm ci first (mapshaper is an offline dev dependency)')
    # Interval in projected metres; mapshaper builds common arcs before simplifying.
    output=PROCESSED/f'simplified_{year}.geojson'
    subprocess.run(['node',str(cli),str(source),'-proj','from=EPSG:3006','EPSG:3006','-snap','interval=0.01','-clean','gap-fill-area=0','-simplify','weighted','interval=15','keep-shapes','-proj','EPSG:4326','-o',str(output),'format=geojson','precision=0.0000001','force'],check=True)
    g=gpd.read_file(output)
    repairs=int((~g.is_valid).sum())
    g.geometry=g.geometry.make_valid().set_precision(0.000001)
    g.to_file(output,driver='GeoJSON')
    if set(g.district_id)!=set(original.district_id) or not g.is_valid.all() or g.is_empty.any(): raise ValueError('Simplification invalid')
    content=json.loads(g.to_json())
    def rounded(x):
        return [rounded(v) for v in x] if isinstance(x,list) else round(x,6)
    for f in content['features']: f['geometry']['coordinates']=rounded(f['geometry']['coordinates'])
    for f in content['features']: f['id']=f['properties']['district_id']
    raw=json.dumps(content,separators=(',',':'),ensure_ascii=False).encode()
    print('Uncompressed size:',len(raw),flush=True)
    if len(raw)>20_000_000: raise ValueError('GeoJSON exceeds 20 MB: use PMTiles or reduce tolerance only after geometric QA')
    (PUBLIC/f'{year}/districts.geojson.gz').write_bytes(gzip.compress(raw,mtime=0))
    projected=g.to_crs(3006).set_index('district_id');orig=original.set_index('district_id')
    relative=(projected.area-orig.area).abs()/orig.area
    write_json(PROCESSED/('geometry_quality.json' if year==2022 else f'geometry_quality_{year}.json'),{'post_rounding_repairs':repairs,'tolerance_m':15,'method':'mapshaper weighted shared arcs, keep-shapes','bytes_uncompressed':len(raw),'bytes_gzip':(PUBLIC/f'{year}/districts.geojson.gz').stat().st_size,'invalid_geometries':int((~g.is_valid).sum()),'p99_relative_area_change':float(relative.quantile(.99)),'maximum_relative_area_change':float(relative.max()),'districts_area_change_above_1pct':relative[relative>.01].to_dict()})
    print('Web geometry:',len(raw),'bytes;', (PUBLIC/f'{year}/districts.geojson.gz').stat().st_size,'compressed',flush=True)
if __name__=='__main__': main()




