"""Group published SCB country cells geographically, retaining missing-cell coverage."""
from common import *
from html.parser import HTMLParser
import gzip,pandas as pd
UN_URL='https://unstats.un.org/unsd/methodology/m49/overview/'
RELIGION_URL='https://www.myndighetensst.se/bidrag/bidragsstatistik'
class TableRows(HTMLParser):
    def __init__(self):super().__init__();self.rows=[];self.row=[];self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[]
        if tag in ['td','th']:self.cell=[]
    def handle_data(self,text):
        if self.cell is not None:self.cell.append(text)
    def handle_endtag(self,tag):
        if tag in ['td','th'] and self.cell is not None:self.row.append(' '.join(''.join(self.cell).split()));self.cell=None
        if tag=='tr':self.rows.append(self.row)

def aggregate_groups(counts,groups):
    values={};details={}
    for g in groups:
        known=[c for c in g['members'] if isinstance(counts.get(c),(int,float)) and (counts[c]>0 or c in ['SE','ÖOF','OVFOD'])]
        missing=[c for c in g['members'] if c not in known]
        values[g['code']]=sum(counts[c] for c in known) if known else None
        details[g['code']]={'published_country_count':len(known),'missing_country_count':len(missing),'missing_country_codes':missing,'member_count':len(g['members']),'status':'published_cell_subtotal' if known else 'missing'}
    return values,details

def main():
    folder=PUBLIC/'countries';data=json.loads(gzip.decompress((folder/'birth_2025.json.gz').read_bytes()))
    raw=cache(UN_URL,'scb/countries/un_m49_overview.html');parser=TableRows();parser.feed(raw.read_text())
    mapping={r[10]:{'continent':r[2],'subregion':r[4],'name_en':r[8],'method':'UN M49'} for r in parser.rows if len(r)==15 and r[1]=='World' and r[10]}
    # SCB includes historical or separately coded places absent from the current M49 rows.
    exceptions={'YU':('150','039'),'CS':('150','039'),'QT':('150','151'),'XK':('150','039'),'TW':('142','030')}
    for code,(continent,subregion) in exceptions.items():mapping[code]={'continent':continent,'subregion':subregion,'method':'Explicit geographic crosswalk for SCB country code'}
    for code in ['SU','ÖOF','OVFOD']:mapping[code]={'continent':'unassigned','subregion':'unassigned','method':'Transcontinental historical country, unknown, or pooled countries; do not allocate'}
    codes=[c['code'] for c in data['countries']]
    if not set(codes)<=set(mapping):raise ValueError('Unmapped country codes '+str(set(codes)-set(mapping)))
    definitions=[('REG_NON_EUROPE','Fuera de Europa',lambda c:mapping[c]['continent'] in ['002','019','142','009']),('REG_AFRICA','África',lambda c:mapping[c]['continent']=='002'),('REG_ASIA','Asia',lambda c:mapping[c]['continent']=='142'),('REG_EUROPE_EX_SE','Europa (sin Suecia)',lambda c:mapping[c]['continent']=='150' and c!='SE'),('REG_EUROPE','Europa (incluye Suecia)',lambda c:mapping[c]['continent']=='150'),('REG_AMERICAS','América',lambda c:mapping[c]['continent']=='019'),('REG_NORTHERN_AMERICA','América septentrional',lambda c:mapping[c]['subregion']=='021'),('REG_LATIN_AMERICA','América Latina y Caribe',lambda c:mapping[c]['subregion']=='419'),('REG_OCEANIA','Oceanía',lambda c:mapping[c]['continent']=='009'),('REG_UNASSIGNED','Sin asignación continental',lambda c:mapping[c]['continent']=='unassigned')]
    groups=[{'code':code,'name_sv':name,'name_es':name,'kind':'region','members':[c for c in codes if predicate(c)],'measure':'Suma de las celdas de países publicadas; subtotal, no total continental completo'} for code,name,predicate in definitions]
    main_groups=[g for g in groups if g['code'] in ['REG_AFRICA','REG_ASIA','REG_EUROPE','REG_AMERICAS','REG_OCEANIA','REG_UNASSIGNED']]
    flat=[c for g in main_groups for c in g['members']]
    if len(flat)!=len(set(flat)) or set(flat)!=set(codes):raise ValueError('Continental partition overlaps or misses countries')
    records=[]
    for r in data['regions']:
        values,details=aggregate_groups(r['counts'],groups);r['counts'].update(values);r['group_details']=details
        for g in groups:
            n=values[g['code']]
            records.append({'region_code':r['code'],'region_name':r['name'],'geographic_level':r['level'],'birth_group_code':g['code'],'birth_group_name':g['name_es'],'reference_date':'2025-12-31','published_cell_subtotal':n,'population_denominator':r['population'],'pct_published_subtotal':100*n/r['population'] if n is not None else None,**{k:v for k,v in details[g['code']].items() if k!='missing_country_codes'},'missing_country_codes':';'.join(details[g['code']]['missing_country_codes']),'source_url':data['source_url'],'classification_url':UN_URL})
    csv=pd.DataFrame(records)
    if not csv.pct_published_subtotal.dropna().between(0,100).all():raise ValueError('Group subtotal percentage outside [0,100]')
    info={'source_url':UN_URL,'classification':'UN M49 continents, with explicit SCB historical-code crosswalk','country_mapping':{c:mapping[c] for c in codes},'groups':groups,'notes':['Türkiye, Cyprus and the South Caucasus are in Asia; Russia in Europe (M49). This differs from some SCB demographic groupings.','Former USSR stays unassigned because its birthplace cannot be divided between Europe and Asia.','Non-Europe is the union of Africa, Asia, Americas and Oceania; unknown and pooled countries are excluded. It is not non-EU.','Groups overlap: non-Europe contains other continental groups; Europe including Sweden contains Europe excluding Sweden. Do not sum every group.','Subtotals include only published country cells. Missing/suppressed cells are tracked; pooled other countries cannot be split by continent. CKM adds uncertainty, so these are not exact lower confidence bounds or exhaustive continental totals.']}
    data['birth_groups']=groups;data['birth_group_classification']=info
    data['religion']={'status':'unavailable_comparable_municipal_data','requested_categories':['Musulmanes','Cristianos','Hindúes'],'source_url':RELIGION_URL,'explanation':'La tabla SCB de nacimiento no registra religión. SST publica miembros y participantes de comunidades subvencionables, un universo distinto de todos los residentes. No se deduce religión por país ni se interpreta nacido en India como hindú.'}
    (folder/'birth_2025.json.gz').write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode(),mtime=0))
    csv.to_csv(folder/'birth_regions_2025.csv',index=False,float_format='%.6f')
    write_json(folder/'birth_regions_definition.json',info)
    provenance=json.loads((folder/'provenance.json').read_text());provenance.update({'birth_groups':len(groups),'classification_source_url':UN_URL,'classification_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'group_measure':'Subtotal of published country cells; missing countries and unknown continental allocation retained','religion':data['religion']});write_json(folder/'provenance.json',provenance)
    print('Geographic groups:',len(groups),'regions:',len(data['regions']),'subtotal observations:',len(csv),flush=True)
if __name__=='__main__':main()
