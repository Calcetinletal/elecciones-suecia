"""Shared paths and immutable, auditable HTTP cache."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, time
import requests
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
PROCESSED = ROOT / 'data/processed'
PUBLIC = ROOT / 'public/data'
SOURCES = json.loads((ROOT / 'config/sources.json').read_text(encoding='utf-8-sig'))
PARTIES = ['S','M','SD','V','C','KD','L','MP','other']
for path in [RAW, PROCESSED, PUBLIC]: path.mkdir(parents=True, exist_ok=True)

def cache(url, relative, payload=None):
    path = RAW / relative
    meta = path.with_suffix(path.suffix + '.metadata.json')
    if path.exists():
        if not meta.exists(): raise ValueError(f'Cache without provenance: {path}')
        info = json.loads(meta.read_text())
        if info['url'] != url or info.get('request') != payload: raise ValueError(f'Cache request changed: {path}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != info['sha256']: raise ValueError(f'Raw modified: {path}')
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        response = requests.get(url,timeout=240) if payload is None else requests.post(url,json=payload,timeout=240)
        if response.status_code not in [429,502,503,504]: break
        time.sleep(3*(attempt+1))
    response.raise_for_status()
    content=response.content
    if content.startswith(b'<?xml') and b'ExceptionReport' in content[:500]: raise ValueError(content[:1000])
    temp=path.with_suffix(path.suffix+'.part'); temp.write_bytes(content); temp.replace(path)
    meta.write_text(json.dumps({'url':url,'request':payload,'downloaded_at':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content),'content_type':response.headers.get('Content-Type')},indent=2,ensure_ascii=False))
    print(f'Downloaded {relative}: {len(content):,} bytes',flush=True)
    return path

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
