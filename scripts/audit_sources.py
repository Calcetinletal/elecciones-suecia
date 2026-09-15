"""Reproduce the small source audit. Does not crawl district pages."""
from common import *
import re
from urllib.parse import urljoin
URLS={
 'val':'https://www.val.se/valresultat-och-statistik/statistik-och-data/radata-fran-val-2002-2022',
 'svt':'https://valresultat.svt.se/2022/',
 'svt_analysis':'https://www.svt.se/datajournalistik/val2022/sa-rostade-svenskarna/',
 'svt_main':'https://valresultat.svt.se/2022/assets/main-d5dc73c5371259c7bab0.js',
 'svt_scatter':'https://www.svt.se/datajournalistik/val2022/sa-rostade-svenskarna/BOB-efterval22-app_scatter-bundle-14.js',
}
def main():
 for name,url in URLS.items():
  extension='.js' if name in ['svt_main','svt_scatter'] else '.html'
  path=cache(url,'audit/'+name+extension)
  text=path.read_text()
  if extension=='.html':
   links=[urljoin(url,x) for x in re.findall(r'(?:href|src)="([^"]+)"',text)]
   print(name,[x for x in links if any(ext in x for ext in ['.zip','.xlsx','.js'])])
  else:
   print(name,len(text),'characters; embedded table:', 'columns:[' in text and 'index:[' in text and 'data:[' in text)
if __name__=='__main__':main()
