from common import *
from concurrent.futures import ThreadPoolExecutor

def inspect(name):
    url=SOURCES['api_base']+SOURCES['tables'][name]
    p=cache(url,f'scb/{name}_metadata.json')
    d=json.loads(p.read_text())
    print(name,[(v['code'],len(v['values']),list(zip(v['values'],v['valueTexts']))[:12] if v['code']!='Region' else v['values'][:4]) for v in d['variables']],flush=True)
if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(inspect,SOURCES['tables']))
        list(pool.map(lambda key: cache(SOURCES[key],f'scb/{key}.gpkg'),['deso_2018','grid_2022']))
