from common import *
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
if __name__ == '__main__':
    def download(url): return cache(url,'boundaries/2022/'+urlparse(url).path.split('/')[-1])
    with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(download,SOURCES['boundaries_2022']))
