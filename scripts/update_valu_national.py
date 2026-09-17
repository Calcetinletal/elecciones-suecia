"""Archive the official national baseline used by the VALU comparison stars.

Run before plot_valu_2026.py to explicitly refresh the provisional snapshot.
"""
from pathlib import Path
import datetime
import hashlib
import io
import json
import subprocess
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://resultat.val.se/resultatfiler/val2026/p/rd/Val_2026_preliminar_00_RD.zip'
CERT = 'https://resultat.val.se/keys/val-sign-crt.pem'
PARTIES = ['S', 'V', 'MP', 'C', 'L', 'M', 'KD', 'SD']

def main():
    raw = urllib.request.urlopen(URL).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive, tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        (folder/'cert.pem').write_bytes(urllib.request.urlopen(CERT).read())
        subprocess.run(['openssl','x509','-pubkey','-noout','-in',str(folder/'cert.pem'),'-out',str(folder/'key.pem')],check=True)
        documents = {}
        for name in archive.namelist():
            if not name.endswith('.json'): continue
            content = archive.read(name)
            (folder/'document.json').write_bytes(content)
            (folder/'signature').write_bytes(archive.read(name[:-5]+'_sign.sha256'))
            subprocess.run(['openssl','dgst','-sha256','-verify',str(folder/'key.pem'),'-signature',str(folder/'signature'),str(folder/'document.json')],check=True)
            documents[name] = json.loads(content)
    national = documents['Val_2026_preliminar_mandatfordelning_00_RD.json']
    districts = documents['Val_2026_preliminar_rostfordelning_00_RD.json']
    assert not national.get('test') and national['valtillfalle']=='Val_2026' and national['valtyp']=='RD'
    assert national['rakningstillfalle']=='preliminär'
    area = national['valomrade']
    assert area['kod']=='00'
    result = area['rostfordelning']['rosterPaverkaMandat']
    counts = {p['partiforkortning']:p['antalRoster'] for p in result['partiRoster']}
    other = result['rosterOvrigaPartier']['antalRoster']
    assert set(counts)==set(PARTIES) and sum(counts.values())+other==result['antalRoster']
    # Includes collection units (late/overseas votes), unlike territorial maps.
    reported = [d['rostfordelning']['rosterPaverkaMandat'] for d in districts['valdistrikt'] if d.get('rostfordelning')]
    assert sum(d['antalRoster'] for d in reported)==result['antalRoster']
    for party in PARTIES:
        assert sum(p['antalRoster'] for d in reported for p in d['partiRoster'] if p['partiforkortning']==party)==counts[party]
    snapshot = dict(source=URL,source_page='https://resultat.val.se/val2026/RD?r=P',
        retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_updated_at=national['senasteUppdateringstid'],source_timezone='Europe/Stockholm',
        source_sha256=hashlib.sha256(raw).hexdigest(),signatures_verified=True,
        election_year=2026,status='provisional',reported_units=area['antalValdistriktRaknade'],
        total_units=area['antalValdistriktSomSkaRaknas'],valid_votes=result['antalRoster'],
        other_votes=other,party_votes=counts,
        scope='National Riksdag result, including reporting collection units; denominator: valid votes')
    target=ROOT/'scripts/data/valu-2026-national-result.json'
    target.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(snapshot,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
