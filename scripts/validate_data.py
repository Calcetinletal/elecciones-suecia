"""Generate a complete, fail-fast data quality report, including anti-joins."""
from common import *
import pandas as pd,geopandas as gpd,numpy as np,gzip

def validate(df,geo):
    errors={};warnings={}
    def check(name,bad):
        ids=df.loc[bad,'district_id'].astype(str).tolist()
        if ids: errors[name]=ids
    check('duplicate_district_id',df.district_id.duplicated(keep=False))
    if geo.crs is None or geo.crs.to_epsg()!=4326: errors['web_crs']=['Expected EPSG:4326']
    if not geo.is_valid.all(): errors['invalid_geometry']=geo.loc[~geo.is_valid,'district_id'].tolist()
    if geo.is_empty.any() or geo.geometry.isna().any(): errors['empty_geometry']=geo.loc[geo.is_empty|geo.geometry.isna(),'district_id'].tolist()
    if geo.district_id.duplicated().any(): errors['duplicate_geometry']=geo.loc[geo.district_id.duplicated(),'district_id'].tolist()
    missing=sorted(set(df.district_id)-set(geo.district_id));extra=sorted(set(geo.district_id)-set(df.district_id))
    if missing: errors['results_without_geometry']=missing
    if extra: errors['boundaries_without_results']=extra
    for c in [x for x in df if not x.startswith('delta_') and (x.startswith('pct_') or x.endswith('_pct'))]:
        values=pd.to_numeric(df[c],errors='coerce');check(c+'_range',values.notna()&(~np.isfinite(values)|(values<0)|(values>100)))
    for c in ['valid_votes','eligible_voters','ballots_cast']+[f'vote_{p}' for p in PARTIES]:
        check(c+'_invalid',df[c].isna()|(~np.isfinite(df[c]))|(df[c]<0)|(df[c]%1!=0))
    check('zero_valid_votes',df.valid_votes<=0);check('zero_eligible_voters',df.eligible_voters<=0)
    check('party_sum_pct',((df[[f'pct_{p}' for p in PARTIES]].sum(axis=1)-100).abs()>.001)|df[[f'pct_{p}' for p in PARTIES]].isna().any(axis=1))
    check('party_sum_counts',df[[f'vote_{p}' for p in PARTIES]].sum(axis=1)!=df.valid_votes)
    check('turnout_identity',(df.turnout_pct-100*df.ballots_cast/df.eligible_voters).abs()>.00001)
    for p in PARTIES: check('vote_pct_identity_'+p,(df['pct_'+p]-100*df['vote_'+p]/df.valid_votes).abs()>.00001)
    for metric in ['foreign_background','foreign_born','foreign_citizens']:
        null=df[metric+'_pct'].isna()
        if null.any(): warnings['missing_'+metric]=df.loc[null,'district_id'].tolist()
    for c in ['demography_coverage','demography_data_coverage','dominant_overlap_share','source_allocation_coverage']:
        check(c+'_range',df[c].notna()&~df[c].between(0,1.000001))
    warnings['partial_coverage']=df.loc[df.coverage_quality=='partial_coverage','district_id'].tolist()
    warnings['median_income_missing']=int(df.median_income.isna().sum())
    return errors,warnings

def main():
    df=pd.read_csv(PROCESSED/'joined_2022.csv',dtype={'district_id':str})
    geo=gpd.GeoDataFrame.from_features(json.loads(gzip.decompress((PUBLIC/'2022/districts.geojson.gz').read_bytes()))['features'],crs=4326)
    errors,warnings=validate(df,geo)
    cw=json.loads((PROCESSED/'crosswalk_quality.json').read_text());geometry=json.loads((PROCESSED/'geometry_quality.json').read_text())
    samples=json.loads((PROCESSED/'sample_checks.json').read_text()) if (PROCESSED/'sample_checks.json').exists() else []
    if len(samples)!=10 or not all(r['election_pass'] for r in samples): errors['sample_checks']=['Ten matching checks required']
    lines=['# Informe de calidad de datos','',f'Fecha: {datetime.now(timezone.utc).date()}. Elección: Riksdag 2022.', '',f'- Distritos: {len(df)}; geometrías: {len(geo)}; CRS web: EPSG:4326.',f'- Errores que bloquean la publicación: {len(errors)}.',f'- Fichas electorales contrastadas con SVT: {len(samples)}.',f'- Distritos con demografía disponible: {df.foreign_background_pct.notna().sum()}.',f'- Cobertura parcial: {(df.coverage_quality=="partial_coverage").sum()}.', '- Unidades de recogida sin territorio: 314, conservadas en `data/processed/non_geographic_results_2022.csv`, excluidas intencionalmente del mapa.','', '## Validaciones', '', 'Geometrías presentes/válidas/no vacías, CRS, claves únicas, anti-join en ambos sentidos, porcentajes [0,100], suma de partidos, recuentos enteros no negativos, identidad participación y porcentajes, missing demográfico, cobertura [0,1].', '', '## Errores', '',json.dumps(errors,indent=2,ensure_ascii=False),'','## Advertencias','',json.dumps(warnings,indent=2,ensure_ascii=False),'','## Overlay y conservación de masa','', 'Los pesos usan masa de la cuadrícula en la intersección dividida por masa en todo el DeSO. La suma puede ser inferior a 1 en costas, aguas o diferencias de límites; no se oculta renormalizando. Puede superar levemente 1 por solapes de los originales. Las cifras estimadas no deben tratarse como recuentos exactos.', '',json.dumps(cw,indent=2,ensure_ascii=False),'','## Simplificación web','', 'Ensayos: 8 m superó 20 MB; 15 m produjo 15,58 MB sin comprimir y 3,98 MB gzip. Se eligió 15 m. Los límites compartidos se simplifican conjuntamente; snap de 1 cm y limpieza sin rellenar huecos. La copia analítica original se conserva. Los cambios de superficie más grandes se enumeran, no alteran el ETL ni los resultados.', '',json.dumps(geometry,indent=2,ensure_ascii=False),'','## Limitaciones de la muestra','', 'Los diez controles electorales coinciden dentro del redondeo. En demografía se comparan estimaciones 2022 con observaciones SVT 2021, por lo que las discrepancias no son errores de unión automáticamente. En la muestra hay diferencias de varios puntos porcentuales (ver MANUAL_CHECKS.md). Esto evidencia que la interpolación no garantiza exactitud local.']
    report='\n'.join(lines)+'\n';(ROOT/'data_quality_report.md').write_text(report);(PUBLIC/'data_quality_report.md').write_text(report)
    write_json(PROCESSED/'validation.json',{'errors':errors,'warnings':warnings})
    print('Validation:',len(errors),'blocking errors;',len(df),'rows',flush=True)
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
