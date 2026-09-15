"""Reproducible 2026 preliminary snapshot + SCB 2025. No runtime APIs."""
from common import *
import argparse, gzip, re, zipfile, subprocess
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.ops import unary_union
from concurrent.futures import ThreadPoolExecutor
from download_demography import jsonstat_frame
from build_crosswalk import build
from build_dataset import aggregate_demography
from simplify_geometries import main as simplify
from validate_data import validate

BASE='https://resultat.val.se/resultatfiler/val2026/'
RESULT='p/rd/Val_2026_preliminar_00_RD.zip'
BOUNDARIES='https://www.val.se/download/18.332cf48819bd61ac1513889/1785491689960/valdistrikt-riket-2026.zip'
COMPARABILITY='https://www.val.se/download/18.1a2972da19f159e73fd3a47/1787064655347/valdistrikt-jamforelser-mellan-2022-och-2026.xlsx'
SCB='https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__BE__BE0101__BE0101Y/FolkmDesoBakgrKon/'
SPECS={'background':('UtlBakgrund',['1','SA']), 'birth':('Fodelseregion',['sv','tot']), 'citizenship':('Medborgarskap',['sv','SA'])}

def polygon_only(geometry):
    if geometry.geom_type in ['Polygon','MultiPolygon']:return geometry
    return unary_union([polygon_only(part) for part in geometry.geoms if part.geom_type in ['Polygon','MultiPolygon','GeometryCollection']])

def download_demography():
    def table(name):
        dimension,values=SPECS[name];url=SOURCES['api_base']+SOURCES['tables'][name]
        meta=json.loads(cache(url,f'scb/2025/{name}_metadata.json').read_text())
        query=[]
        for v in meta['variables']:
            code=v['code']
            selected=[x for x in v['values'] if re.fullmatch(r'\d{4}[ABC]\d{4}_DeSO2025',x)] if code=='Region' else ['2025'] if code=='Tid' else ['1+2'] if code=='Kon' else values if code==dimension else v['values']
            if not selected or not set(selected)<=set(v['values']): raise ValueError('Invalid SCB selection '+code)
            query.append({'code':code,'selection':{'filter':'item','values':selected}})
        payload={'query':query,'response':{'format':'json-stat2'}}
        raw=cache(url,f'scb/2025/{name}_2025.json',payload)
        frame=jsonstat_frame(json.loads(raw.read_text())).pivot(index='Region',columns=dimension,values='value')
        frame.index=frame.index.str.replace('_DeSO2025','',regex=False);frame.index.name='deso_id'
        return name,frame
    with ThreadPoolExecutor(max_workers=3) as pool: frames=dict(pool.map(table,SPECS))
    b=frames['background'];out=pd.DataFrame(index=b.index)
    out['population']=b['SA'];out['foreign_background_count']=b['1']
    out['birth_population']=frames['birth']['tot'];out['foreign_born_count']=frames['birth']['tot']-frames['birth']['sv']
    out['citizenship_population']=frames['citizenship']['SA'];out['foreign_citizens_count']=frames['citizenship']['SA']-frames['citizenship']['sv']
    # No substitution of 2022 socioeconomic controls into the 2025 edition.
    for c in ['education_population','higher_education_count','employment_population','employed_count']:out[c]=np.nan
    for num,den in [('foreign_background_count','population'),('foreign_born_count','birth_population'),('foreign_citizens_count','citizenship_population')]:
        if ((out[num]<0)|(out[num]>out[den])).any(): raise ValueError('SCB protected counts outside valid range; inspect before publishing')
    out.to_csv(PROCESSED/'deso_demography_2025.csv')
    for key,layer in [('deso_2025','DeSO_2025'),('grid_2025','befolkning_1km_2025')]:
        cache('https://geodata.scb.se/geoserver/stat/wfs?service=WFS&REQUEST=GetFeature&version=1.1.0&outputFormat=geopackage&TYPENAMES=stat:'+layer,'scb/2025/'+key+'.gpkg')
    return out.reset_index()

def normalize_results(data,geo):
    if data.get('test') or data.get('valtillfalle')!='Val_2026' or data.get('valtyp')!='RD' or data.get('rakningstillfalle')!='preliminär': raise ValueError('Not actual preliminary Riksdag 2026 data')
    districts=[d for d in data['valdistrikt'] if d['valdistriktstyp']=='valdistrikt']
    if len({d['valdistriktskod'] for d in districts})!=len(districts):raise ValueError('Duplicate results')
    if {d['valdistriktskod'] for d in districts}!=set(geo.district_id):raise ValueError('Geometry/result anti-join failed')
    records=[]
    for d in districts:
        r={'district_id':d['valdistriktskod'],'election_year':2026,'geometry_year':2026,'election_status':'provisional','election_reported':bool(d['rostfordelning']),'reported_at':d['rapporteringsTid'],'eligible_voters':d['antalRostberattigade'],'ballots_cast':None,'valid_votes':None,'turnout_pct':None,'winning_party':None,'winning_party_pct':None,'winning_party_tie':False,'winning_party_name':None}
        for p in PARTIES:r['vote_'+p]=None;r['pct_'+p]=None
        if r['election_reported']:
            valid=d['rostfordelning']['rosterPaverkaMandat'];r['valid_votes']=valid['antalRoster'];r['ballots_cast']=d['totaltAntalRoster']
            r['turnout_pct']=100*r['ballots_cast']/r['eligible_voters']
            for p in PARTIES:r['vote_'+p]=0
            party_rows=valid['partiRoster']
            for p in party_rows:
                key=p['partiforkortning'] if p['partiforkortning'] in PARTIES[:-1] else 'other'
                r['vote_'+key]+=p['antalRoster']
            r['vote_other']+=valid['rosterOvrigaPartier']['antalRoster']
            if sum(r['vote_'+p] for p in PARTIES)!=r['valid_votes']:raise ValueError('Party sum mismatch')
            for p in PARTIES:r['pct_'+p]=100*r['vote_'+p]/r['valid_votes']
            winner=max(party_rows,key=lambda p:p['antalRoster'])
            # Other is an aggregate, so it cannot itself win. If its total is greater,
            # an individual winner cannot be established from preliminary categories.
            if winner['antalRoster']>r['vote_other']:
                r['winning_party']=winner['partiforkortning'];r['winning_party_name']=winner['partibeteckning'];r['winning_party_pct']=100*winner['antalRoster']/r['valid_votes'];r['winning_party_tie']=sum(p['antalRoster']==winner['antalRoster'] for p in party_rows)>1
            if abs(r['turnout_pct']-d['valdeltagandeVallokal'])>.051:raise ValueError('Published turnout mismatch')
            for p in party_rows:
                if abs(100*p['antalRoster']/r['valid_votes']-p['andelRoster'])>.051:raise ValueError('Published party share mismatch')
        records.append(r)
    return geo.drop(columns='geometry').merge(pd.DataFrame(records),on='district_id',validate='one_to_one')

def add_comparisons(new,old,official,data):
    cw=official.copy();cw.columns=['new_id','name','municipality','county','status','old_id','old_id_2']
    for col in ['new_id','old_id','old_id_2']:cw[col]=cw[col].map(lambda v:'' if pd.isna(v) else str(int(v)).zfill(8))
    if cw.new_id.duplicated().any() or set(cw.new_id)!=set(new.district_id):raise ValueError('Incomplete official comparability')
    out=new.set_index('district_id').copy();previous=old.set_index('district_id');live={d['valdistriktskod']:d for d in data['valdistrikt']}
    for metric in ['pct_S','pct_SD','pct_M','turnout_pct']:out['delta_'+metric]=np.nan
    out['comparison_status']='not_comparable';out['comparison_source_url']=COMPARABILITY;out['comparison_old_ids']=''
    for r in cw.itertuples():
        ids=[x for x in [r.old_id,r.old_id_2] if x]
        current=live[r.new_id]
        if r.status not in ['Kan jämföras','Kan jämföras mot flera']:continue
        if not ids or len(set(ids))!=len(ids) or not set(ids)<=set(previous.index):raise ValueError('Unknown old IDs')
        # Require agreement between the August official assessment and the live file.
        expected_live='Jämförs mot summerat' if r.status=='Kan jämföras mot flera' else r.status
        if current['statusJamforelse']!=expected_live or set(current['valdistriktskodForegaendeVal'] or [])!=set(ids):
            out.loc[r.new_id,'comparison_status']='source_disagreement';continue
        out.loc[r.new_id,'comparison_status']='comparable' if len(ids)==1 else 'comparable_aggregate'
        out.loc[r.new_id,'comparison_old_ids']=';'.join(ids)
        prior=previous.loc[ids]
        for p in ['S','SD','M']:out.loc[r.new_id,'delta_pct_'+p]=out.loc[r.new_id,'pct_'+p]-100*prior['vote_'+p].sum()/prior.valid_votes.sum()
        out.loc[r.new_id,'delta_turnout_pct']=out.loc[r.new_id,'turnout_pct']-100*prior.ballots_cast.sum()/prior.eligible_voters.sum()
    return out.reset_index(),cw

def verify_signatures(path):
    cert=cache('https://resultat.val.se/keys/val-sign-crt.pem','val2026/val-sign-crt.pem')
    folder=PROCESSED/'signature_check_2026';folder.mkdir(exist_ok=True)
    key=folder/'public.pem'
    subprocess.run(['openssl','x509','-pubkey','-noout','-in',str(cert),'-out',str(key)],check=True)
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith('.json'):continue
            doc=folder/Path(name).name;sig=folder/(doc.stem+'_sign.sha256');doc.write_bytes(z.read(name));sig.write_bytes(z.read(doc.stem+'_sign.sha256'))
            subprocess.run(['openssl','dgst','-sha256','-verify',str(key),'-signature',str(sig),str(doc)],check=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',default='2026-09-14',help='Unique cache label. Reuse to reproduce; new label to refresh results.');p.add_argument('--reuse-crosswalk',action='store_true',help='Reuse already computed overlay of fixed 2026 / 2025 geometries');args=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.snapshot):raise ValueError('Invalid snapshot label')
    prefix='val2026/'+args.snapshot+'/'
    urls={'index.md5':BASE+'index.md5','results.zip':BASE+RESULT,'boundaries.zip':BOUNDARIES,'comparability.xlsx':COMPARABILITY}
    with ThreadPoolExecutor(max_workers=3) as pool:paths=dict(pool.map(lambda item:(item[0],cache(item[1],prefix+item[0])),urls.items()))
    checks={line.split()[1].removeprefix('./'):line.split()[0] for line in paths['index.md5'].read_text().splitlines()}
    if checks.get(RESULT)!=hashlib.md5(paths['results.zip'].read_bytes()).hexdigest():raise ValueError('Index/result changed during download; retry with a new snapshot label')
    verify_signatures(paths['results.zip'])
    with zipfile.ZipFile(paths['results.zip']) as z:data=json.loads(z.read('Val_2026_preliminar_rostfordelning_00_RD.json'))
    with zipfile.ZipFile(paths['boundaries.zip']) as z:rawgeo=json.loads(z.read(z.namelist()[0]))
    if '3006' not in str(rawgeo.get('crs')):raise ValueError('Expected SWEREF99 TM geometry')
    geo=gpd.GeoDataFrame.from_features(rawgeo['features'],crs=3006).rename(columns={'Valdistriktskod':'district_id','Valdistriktsnamn':'district_name','Länskod':'county_code','Län':'county_name','Kommunkod':'municipality_code','Kommun':'municipality_name'})
    geo=geo[['district_id','district_name','county_code','county_name','municipality_code','municipality_name','geometry']]
    if geo.district_id.duplicated().any():raise ValueError('Duplicate geometry')
    repairs=int((~geo.is_valid).sum());geo.geometry=geo.geometry.make_valid().map(polygon_only);geo.to_parquet(PROCESSED/'boundaries_2026.parquet')
    election=normalize_results(data,geo)
    write_json(PROCESSED/'non_geographic_results_2026.json',[d for d in data['valdistrikt'] if d['valdistriktstyp']!='valdistrikt'])
    demo=download_demography()
    cwpath=PROCESSED/'crosswalk_2026.parquet'
    if args.reuse_crosswalk and cwpath.exists():cw=pd.read_parquet(cwpath)
    else:
        deso=gpd.read_file(RAW/'scb/2025/deso_2025.gpkg').rename(columns={'desokod':'deso_id'})
        grid=gpd.read_file(RAW/'scb/2025/grid_2025.gpkg').rename(columns={'beftotalt':'population'})
        if set(deso.deso_id)!=set(demo.deso_id):raise ValueError('DeSO geometry/statistics anti-join failed')
        cw=build(deso,geo,grid);cw.to_parquet(cwpath,index=False)
    values=aggregate_demography(demo,cw,2025)
    out=election.merge(values,on='district_id',how='left',validate='one_to_one')
    out.demography_method=out.demography_method.fillna('missing');out.coverage_quality=out.coverage_quality.fillna('missing')
    out['election_source']='Valmyndigheten: preliminary Riksdag 2026';out['election_source_url']=BASE+RESULT
    out['demography_source']='SCB: population 2025-12-31 / DeSO 2025 / CKM disclosure protection';out['demography_source_url']=SCB
    source_meta=json.loads(paths['results.zip'].with_suffix('.zip.metadata.json').read_text())
    out['election_downloaded_at']=source_meta['downloaded_at'];out['election_updated_at']=data['senasteUppdateringstid'];out['demography_reference_date']='2025-12-31'
    out['education_year']=None;out['employment_year']=None
    old=pd.read_csv(PROCESSED/'joined_2022.csv',dtype={'district_id':str})
    out,comparison=add_comparisons(out,old,pd.read_excel(paths['comparability.xlsx'],sheet_name='Jämförelser'),data)
    for name,parties in json.loads((ROOT/'config/blocks.json').read_text())['2026'].items():out[name]=out[[f'pct_{x}' for x in parties]].sum(axis=1,min_count=len(parties))
    folder=PUBLIC/'2026';folder.mkdir(exist_ok=True)
    simplify(2026)
    webgeo=gpd.GeoDataFrame.from_features(json.loads(gzip.decompress((folder/'districts.geojson.gz').read_bytes()))['features'],crs=4326)
    reported=out[out.election_reported].copy()
    if len(reported)!=data['antalValdistriktRaknade']:raise ValueError('Reported district count mismatch')
    errors,warnings=validate(reported,webgeo[webgeo.district_id.isin(reported.district_id)])
    pending=out[~out.election_reported]
    if pending[['valid_votes','ballots_cast','turnout_pct']+[f'pct_{p}' for p in PARTIES]].notna().any().any():errors['pending_fabricated_results']=True
    if len(out)!=len(webgeo) or out.district_id.duplicated().any():errors['full_join']=True
    for col in ['foreign_background_pct','foreign_born_pct','foreign_citizens_pct']:
        if not out[col].dropna().between(0,100).all():errors['demography_range_'+col]=True
    write_json(PROCESSED/'validation_2026.json',{'errors':errors,'warnings':warnings})
    if errors:raise ValueError(str(errors))
    from build_district_birth_regions import attach_birth_regions
    out=attach_birth_regions(out,2026,cw)
    from build_district_income import attach_income
    out=attach_income(out,2026,cw)
    out=out.sort_values('district_id');out.to_csv(PROCESSED/'joined_2026.csv',index=False,float_format='%.6f');out.to_csv(folder/'joined_2026.csv',index=False,float_format='%.6f')
    (folder/'districts.json.gz').write_bytes(gzip.compress(out.round(6).to_json(orient='records',force_ascii=False).encode(),mtime=0))
    comparison.to_csv(PROCESSED/'comparability_2022_2026.csv',index=False)
    sourceweights=cw.groupby('deso_id').weight.sum()
    meta={'election_year':2026,'status':'provisional','snapshot':args.snapshot,'downloaded_at':source_meta['downloaded_at'],'source_updated_at':data['senasteUppdateringstid'],'source_timezone':'Europe/Stockholm','district_count':len(out),'reported_district_count':len(reported),'pending_district_count':len(pending),'non_geographic_count':len(data['valdistrikt'])-len(out),'demography_year':2025,'demography_reference_date':'2025-12-31','demography_geometry_year':2025,'grid_year':2025,'election_source_url':BASE+RESULT,'geometry_source_url':BOUNDARIES,'comparability_source_url':COMPARABILITY,'demography_source_url':SCB,'license':'Valmyndigheten: free reuse with attribution; SCB: CC0','signatures_verified':True,'election_sha256':source_meta['sha256'],'boundary_repairs':repairs,'intersections':len(cw),'source_weight_min':float(sourceweights.min()),'source_weight_max':float(sourceweights.max()),'areal_fallback_intersections':int(cw.method.eq('areal_estimate').sum()),'coverage_counts':out.coverage_quality.value_counts().to_dict(),'comparison_counts':out.comparison_status.value_counts().to_dict(),'comparable_reported_count':int(out.delta_pct_S.notna().sum()),'scb_disclosure_control':'CKM: independently protected cells; sums may differ from published totals','education_and_employment':'Not included in this 2025 demographic edition'}
    write_json(folder/'provenance.json',meta)
    quality=json.loads((PROCESSED/'geometry_quality_2026.json').read_text())
    report='\n'.join(['# Validación de la edición provisional 2026','',
        f"Descarga UTC: {meta['downloaded_at']}. Fuente actualizada: {meta['source_updated_at']} (Europe/Stockholm).",
        f"Distritos territoriales: {len(out)}. Contabilizados: {len(reported)}. Pendientes: {len(pending)}. Unidades de recogida excluidas del mapa: {meta['non_geographic_count']}.",
        '', '## Comprobaciones realizadas','',
        '- Firmas RSA/SHA-256 de los tres JSON verificadas con el certificado oficial; MD5 del ZIP contrastado con el índice. SHA-256 y petición de cada original conservados.',
        '- Elección real Val_2026 / RD / preliminär; rechaza simulaciones test=true. Fecha electoral y estado preservados.',
        '- Uniones completas uno a uno, sin códigos duplicados. Porcentajes, suma de partidos, recuentos enteros y participación validados en todos los distritos contabilizados; contraste con porcentajes publicados a su precisión de 0,1 pp.',
        '- Los distritos pendientes conservan null en votos y porcentajes. Todos los distritos conservan su geometría y demografía. Las estadísticas excluyen valores ausentes.',
        '- Correspondencias Excel y JSON coinciden después de traducir Kan jämföras mot flera a Jämförs mot summerat. Dos distritos: suma de numeradores y denominadores, nunca media simple de porcentajes.',
        '', '## Demografía y límites','',
        'SCB 31/12/2025, DeSO 2025, cuadrícula de población 1 km 2025. Interpolación espacial por masa poblacional. CKM añade perturbaciones estadísticas; las sumas de celdas pueden diferir de los totales. Cobertura alta no garantiza precisión local. Empleo y educación quedan sin dato en esta edición.',
        'Se repararon seis geometrías analíticas. En las colecciones se conservaron componentes poligonales; los segmentos sin área se excluyeron. Mapshaper avisó de seis intersecciones no reparadas en su fase de simplificación; se validaron y repararon los polígonos finales. Esto no certifica ausencia total de pequeños solapes entre polígonos.',
        '', '## Procedencia y diagnósticos','', '```json',json.dumps(meta,ensure_ascii=False,indent=2),'```','', '## Geometría web','', '```json',json.dumps(quality,ensure_ascii=False,indent=2),'```', '', 'Errores bloqueantes de validación: 0.'])+'\n'
    (folder/'quality_report.md').write_text(report,encoding='utf-8')
    (ROOT/'data_quality_report_2026.md').write_text(report,encoding='utf-8')
    manifest=json.loads((PUBLIC/'manifest.json').read_text());entry={**meta,'table':'2026/districts.json.gz','geometry':'2026/districts.geojson.gz','year':2026}
    manifest['years']=[y for y in manifest['years'] if y['year']!=2026]+[entry];write_json(PUBLIC/'manifest.json',manifest)
    print(json.dumps(meta,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
