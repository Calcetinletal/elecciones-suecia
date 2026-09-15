from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import pytest
from build_crosswalk import build
from import_2026 import compare

def test_real_intersections_differ_from_centroid_and_area():
    d=gpd.GeoDataFrame({'deso_id':['d']},geometry=[box(0,0,1000,1000)],crs=3006)
    v=gpd.GeoDataFrame({'district_id':['left','right']},geometry=[box(0,0,500,1000),box(500,0,1000,1000)],crs=3006)
    grid=gpd.GeoDataFrame({'population':[90,10]},geometry=[box(0,0,500,1000),box(500,0,1000,1000)],crs=3006)
    cw=build(d,v,grid).set_index('district_id')
    assert cw.loc['left','weight']==pytest.approx(.9)
    assert cw.loc['right','weight']==pytest.approx(.1)
    assert cw.weight.sum()==pytest.approx(1)
    assert set(cw.method)=={'population_weighted_estimate'}

def test_area_fallback_is_explicit():
    d=gpd.GeoDataFrame({'deso_id':['d']},geometry=[box(0,0,10,10)],crs=3006)
    v=gpd.GeoDataFrame({'district_id':['v']},geometry=[box(0,0,5,10)],crs=3006)
    cw=build(d,v)
    assert cw.weight.iloc[0]==pytest.approx(.5)
    assert cw.method.iloc[0]=='areal_estimate'

def test_zero_population_grid_fallback():
    d=gpd.GeoDataFrame({'deso_id':['d']},geometry=[box(0,0,10,10)],crs=3006)
    v=gpd.GeoDataFrame({'district_id':['v']},geometry=[box(0,0,10,10)],crs=3006)
    grid=gpd.GeoDataFrame({'population':[0]},geometry=[box(0,0,10,10)],crs=3006)
    assert build(d,v,grid).method.iloc[0]=='areal_estimate'

def fixtures():
    old=pd.DataFrame({'district_id':['a','b','c'],'pct_S':[20,30,40],'pct_SD':[10,15,20],'pct_M':[25,20,15],'turnout_pct':[80,85,90]})
    new=pd.DataFrame({'district_id':['a','b','d'],'pct_S':[25,32,20],'pct_SD':[8,19,15],'pct_M':[28,18,30],'turnout_pct':[78,84,88]})
    cw=pd.DataFrame([['a','a','comparable','https://www.val.se/evidence'],['b','b','changed_boundary',''],['c','','removed',''],['','d','new','']],columns=['old_id','new_id','status','source_url'])
    return old,new,cw

def test_only_officially_comparable_districts_get_deltas():
    old,new,cw=fixtures();result=compare(old,new,cw).set_index('district_id')
    assert result.loc['a','delta_pct_S']==5
    assert result.loc['a','delta_turnout_pct']==-2
    assert pd.isna(result.loc['b','delta_pct_S'])
    assert pd.isna(result.loc['d','delta_pct_S'])

def test_same_code_is_not_evidence():
    old,new,cw=fixtures();cw.loc[0,'source_url']=''
    with pytest.raises(ValueError,match='official'):compare(old,new,cw)

def test_crosswalk_must_classify_every_district():
    old,new,cw=fixtures()
    with pytest.raises(ValueError,match='every'):compare(old,new,cw.iloc[:2])

from build_2026 import normalize_results, add_comparisons
import json,zipfile
ROOT=Path(__file__).resolve().parents[1]

def test_provisional_pending_and_simulation_rejection():
    data=json.loads((ROOT/'tests/fixtures/official_2026_sample.json').read_text())
    ids=[d['valdistriktskod'] for d in data['valdistrikt'] if d['valdistriktstyp']=='valdistrikt']
    geo=gpd.GeoDataFrame({'district_id':ids},geometry=[box(0,0,1,1)]*len(ids),crs=3006)
    out=normalize_results(data,geo)
    assert len(out)==2
    pending=out[~out.election_reported]
    assert len(pending)==1
    assert pending[['valid_votes','pct_SD','turnout_pct','winning_party_pct']].isna().all().all()
    data['test']=True
    with pytest.raises(ValueError,match='Not actual'):normalize_results(data,geo)

def test_official_two_to_one_comparison_aggregates_counts_and_checks_live_evidence():
    old=pd.DataFrame({'district_id':['00000001','00000002'],'vote_S':[20,180],'vote_SD':[10,90],'vote_M':[30,270],'valid_votes':[100,900],'ballots_cast':[100,900],'eligible_voters':[200,1000]})
    new=pd.DataFrame({'district_id':['00000003'],'pct_S':[25.0],'pct_SD':[10.0],'pct_M':[30.0],'turnout_pct':[90.0]})
    cw=pd.DataFrame([[3,'name','municipality','county','Kan jämföras mot flera',1,2]],columns=list('abcdefg'))
    data={'valdistrikt':[{'valdistriktskod':'00000003','statusJamforelse':'Jämförs mot summerat','valdistriktskodForegaendeVal':['00000001','00000002']}]}
    out,_=add_comparisons(new,old,cw,data)
    assert out.delta_pct_S.iloc[0]==5
    assert out.delta_turnout_pct.iloc[0]==pytest.approx(90-100*1000/1200)
    assert out.comparison_status.iloc[0]=='comparable_aggregate'
    data['valdistrikt'][0]['statusJamforelse']='Ej jämförbart'
    out,_=add_comparisons(new,old,cw,data)
    assert out.delta_pct_S.isna().all()
    assert out.comparison_status.iloc[0]=='source_disagreement'

from build_birth_regions import aggregate_groups

def test_birth_region_subtotals_keep_suppression_and_missing_coverage():
    groups=[{'code':'region','members':['ES','FR','DE']},{'code':'empty','members':['IT','GR']}]
    values,details=aggregate_groups({'ES':50,'FR':None,'DE':0,'IT':None},groups)
    assert values=={'region':50,'empty':None}
    assert details['region']['published_country_count']==1
    assert details['region']['missing_country_codes']==['FR','DE']
    assert details['empty']['status']=='missing'

def test_published_birth_group_partition_and_unassigned_cells():
    import gzip
    data=json.loads(gzip.decompress((ROOT/'public/data/countries/birth_2025.json.gz').read_bytes()))
    groups={g['code']:g for g in data['birth_groups']}
    assert len(groups)==10
    assert set(groups['REG_UNASSIGNED']['members'])=={'SU','ÖOF','OVFOD'}
    assert 'TR' in groups['REG_ASIA']['members']
    assert 'RU' in groups['REG_EUROPE']['members']
    assert set(groups['REG_EUROPE']['members'])-set(groups['REG_EUROPE_EX_SE']['members'])=={'SE'}
    assert set(groups['REG_NON_EUROPE']['members'])==set().union(*(set(groups[g]['members']) for g in ['REG_AFRICA','REG_ASIA','REG_AMERICAS','REG_OCEANIA']))
    for region in data['regions']:
        expected,details=aggregate_groups(region['counts'],data['birth_groups'])
        assert all(region['counts'][key]==value for key,value in expected.items())
        assert region['group_details']==details
    assert data['religion']['status']=='unavailable_comparable_municipal_data'

from build_district_birth_regions import estimate_birth_regions, GROUPS

def test_birth_district_estimates_transfer_counts_before_percentages():
    demo=pd.DataFrame({'deso_id':['a','b'],'tot':[100,900],'sv':[50,810],'eu':[30,60],'öv':[20,30]})
    cw=pd.DataFrame({'deso_id':['a','b'],'district_id':['v','v'],'weight':[1.,.5]})
    result=estimate_birth_regions(demo,cw).loc['v']
    assert result.birth_regions_population==550
    assert result.born_europe_ex_sweden_count==60
    assert result.born_europe_ex_sweden_pct==pytest.approx(100*60/550)
    assert result.born_rest_world_unknown_count==35
    assert result.birth_regions_sum_gap==0

def test_birth_district_missing_contributor_is_not_partial_total_or_zero():
    demo=pd.DataFrame({'deso_id':['a','b'],'tot':[100,100],'sv':[70,80],'eu':[20,None],'öv':[10,20]})
    cw=pd.DataFrame({'deso_id':['a','b','a'],'district_id':['partial','partial','complete'],'weight':[.5,1.,.5]})
    result=estimate_birth_regions(demo,cw)
    assert not result.loc['partial','birth_regions_complete']
    assert pd.isna(result.loc['partial','born_europe_ex_sweden_pct'])
    assert pd.isna(result.loc['partial','birth_regions_population'])
    assert result.loc['complete','birth_regions_population']==50
    assert result.loc['complete','born_europe_ex_sweden_pct']==20

def test_birth_district_independent_protected_cells_are_not_normalized():
    demo=pd.DataFrame({'deso_id':['a'],'tot':[100],'sv':[71],'eu':[20],'öv':[10]})
    cw=pd.DataFrame({'deso_id':['a'],'district_id':['v'],'weight':[.4]})
    result=estimate_birth_regions(demo,cw).loc['v']
    assert result.born_sweden_pct==pytest.approx(71)
    assert result.birth_regions_population==40
    assert result.birth_regions_sum_gap==pytest.approx(.4)

def test_published_birth_districts_match_crosswalk_and_all_electoral_keys():
    import gzip
    for election_year,demo_year,expected_count in [(2022,2022,6264),(2026,2025,6312)]:
        rows=pd.DataFrame(json.loads(gzip.decompress((ROOT/f'public/data/{election_year}/districts.json.gz').read_bytes()))).set_index('district_id')
        demo=pd.read_csv(ROOT/f'data/processed/deso_birth_regions_{demo_year}.csv',dtype={'deso_id':str})
        crosswalk=pd.read_parquet(ROOT/f'data/processed/crosswalk_{election_year}.parquet')
        estimates=estimate_birth_regions(demo,crosswalk)
        assert len(rows)==expected_count and set(rows.index)==set(estimates.index)
        assert rows.birth_regions_complete.all()
        for key in [g+'_pct' for g in GROUPS.values()]:
            assert (rows[key].sort_index()-estimates[key].sort_index()).abs().max()<.000001
        assert rows.birth_regions_year.eq(demo_year).all()


def test_parental_groups_match_all_official_cells_without_renormalization():
    import gzip, math
    raw=json.loads((ROOT/'data/raw/scb/parents/parental_background_2025.json').read_text())
    published=json.loads(gzip.decompress((ROOT/'public/data/parents/background_2025.json.gz').read_bytes()))
    def source(region,category):
        selected={'Region':region,'UtlBakgrund':category,'Alder':'tot','Kon':'TotSa','ContentsCode':'0000086U','Tid':'2025'}
        indices=[]
        for dim in raw['id']:
            ix=raw['dimension'][dim]['category']['index']
            indices.append(ix.index(selected[dim]) if isinstance(ix,list) else ix[selected[dim]])
        index=sum(n*math.prod(raw['size'][i+1:]) for i,n in enumerate(indices))
        return raw['value'][index] if isinstance(raw['value'],list) else raw['value'].get(str(index))
    assert len(published['regions'])==312
    assert sum(r['level']=='municipality' for r in published['regions'])==290
    assert {c['source_code'] for c in published['countries']}=={'08','4','5','6'}
    for region in published['regions']:
        assert region['population']==source(region['code'],'TotUI')
        for category in published['countries']:
            assert region['counts'][category['code']]==source(region['code'],category['source_code'])
        assert sum(region['counts'].values())-region['population']==region['component_sum_gap']
    national=next(r for r in published['regions'] if r['code']=='00')
    assert national['population']==10605529
    assert national['counts']['PARENT_MIXED']==845089
    assert national['component_sum_gap']==1
