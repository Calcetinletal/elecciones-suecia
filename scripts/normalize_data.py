"""Normalize authoritative electoral rows and retain non-geographic votes separately."""
from common import *
import pandas as pd, geopandas as gpd, zipfile
MAP={'Arbetarepartiet-Socialdemokraterna':'S','Moderaterna':'M','Sverigedemokraterna':'SD','Vänsterpartiet':'V','Centerpartiet':'C','Kristdemokraterna':'KD','Liberalerna (tidigare Folkpartiet)':'L','Miljöpartiet de gröna':'MP'}
EXCLUDED={'Summa giltiga röster','Valdeltagande','blanka röster','övriga ogiltiga','ej anmält deltagande'}

def normalize_election():
    df=pd.read_excel(RAW/'elections/2022/results.xlsx',sheet_name='roster_RD',dtype={' Valdistriktskod':str})
    df.columns=df.columns.str.strip()
    for c in df.select_dtypes('object'): df[c]=df[c].str.strip()
    df['Röster']=pd.to_numeric(df['Röster'],errors='raise')
    meta=df.drop_duplicates('Distrikt').set_index('Distrikt')
    result=meta[['Valdistriktskod','Valdistriktnamn','Kommun','Län','Röstberättigade']].rename(columns={'Valdistriktskod':'district_id','Valdistriktnamn':'district_name','Kommun':'municipality_name','Län':'county_name','Röstberättigade':'eligible_voters'})
    result['county_code']=result.index.str.split('-').str[1]
    result['municipality_code']=result['county_code']+result.index.str.split('-').str[2]
    for source,target in [('Summa giltiga röster','valid_votes'),('Valdeltagande','ballots_cast')]:
        rows=df[df.Parti==source]
        if rows.Distrikt.duplicated().any(): raise ValueError('Repeated totals')
        result[target]=rows.set_index('Distrikt')['Röster']
    valid=df[~df.Parti.isin(EXCLUDED)].copy();valid['party']=valid.Parti.map(MAP).fillna('other')
    votes=valid.pivot_table(index='Distrikt',columns='party',values='Röster',aggfunc='sum',fill_value=0)
    for party in PARTIES:
        result['vote_'+party]=votes[party].reindex(result.index).fillna(0).astype(int)
        result['pct_'+party]=100*result['vote_'+party]/result['valid_votes']
    if not (result[[f'vote_{p}' for p in PARTIES]].sum(axis=1)==result.valid_votes).all(): raise ValueError('Vote totals disagree')
    result['turnout_pct']=100*result.ballots_cast/result.eligible_voters.replace(0,float('nan'))
    # An aggregate of other parties is never a single candidate for winning party.
    individual=valid.pivot_table(index='Distrikt',columns='Parti',values='Röster',aggfunc='sum',fill_value=0)
    winner=individual.idxmax(axis=1); result['winning_party']=winner.map(MAP).fillna('other')
    result['winning_party_name']=winner
    result['winning_party_pct']=100*individual.max(axis=1)/result.valid_votes
    result['winning_party_tie']=(individual.eq(individual.max(axis=1),axis=0).sum(axis=1)>1)
    result['election_year']=2022;result['geometry_year']=2022
    blocks=json.loads((ROOT/'config/blocks.json').read_text(encoding='utf-8-sig'))['2022']
    for name,parties in blocks.items(): result[name]=result[[f'pct_{p}' for p in parties]].sum(axis=1)
    geographic=result.district_id.str.fullmatch(r'\d{8}') & ~result.district_name.str.contains('Uppsamlingsdistrikt',case=False)
    result[~geographic].to_csv(PROCESSED/'non_geographic_results_2022.csv',index=False)
    result[geographic].to_csv(PROCESSED/'elections_2022.csv',index=False)
    print('Election:',geographic.sum(),'districts;',(~geographic).sum(),'collection units',flush=True)

def normalize_boundaries():
    features=[]
    for path in sorted((RAW/'boundaries/2022').glob('*.zip')):
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name.endswith('.json'): features.extend(json.loads(z.read(name))['features'])
    g=gpd.GeoDataFrame.from_features(features,crs=3006).rename(columns={'Lkfv':'district_id','Vdnamn':'district_name'})
    g['district_id']=g.district_id.astype(str).str.zfill(8)
    invalid=~g.is_valid
    write_json(PROCESSED/'boundary_repairs.json',g.loc[invalid,'district_id'].tolist())
    g.geometry=g.geometry.make_valid()
    g=g[['district_id','district_name','geometry']].dissolve('district_id',as_index=False)
    if not g.is_valid.all() or g.geometry.is_empty.any(): raise ValueError('Invalid boundary')
    g.to_parquet(PROCESSED/'boundaries_2022.parquet')
    print('Boundaries:',len(g),'repaired',invalid.sum(),flush=True)
if __name__=='__main__':
    normalize_election();normalize_boundaries()

