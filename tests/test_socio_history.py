import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pandas as pd
import numpy as np
from build_socio_history import estimate

def test_transfers_numerators_and_their_own_denominators():
    f=pd.DataFrame({'n':[1000000.,9000000.],'d':[10.,30.]},index=['a','b'])
    cw=pd.DataFrame({'district_id':['x','y','x','y'],'deso_id':['a','a','b','b'],'weight':[.8,.2,.2,.8]})
    result=estimate(f,cw)
    assert result.loc['x','n']==2600000
    assert result.loc['x','d']==14
    assert np.isclose(result.n.sum(),f.n.sum())
    assert np.isclose(result.d.sum(),f.d.sum())
    assert result.loc['x','n']/result.loc['x','d']!=.8*100000+.2*300000

def test_missing_contributor_suppresses_whole_district_but_zero_count_is_valid():
    f=pd.DataFrame({'n':[0.,None],'d':[10.,30.]},index=['a','b'])
    cw=pd.DataFrame({'district_id':['x','x','y'],'deso_id':['a','b','a'],'weight':[.5,1.,.5]})
    result=estimate(f,cw)
    assert np.isnan(result.loc['x','n'])
    assert result.loc['y','n']==0
    assert result.loc['y','d']==5

def test_early_partial_deso_is_not_invented_and_population_is_a_count():
    f=pd.DataFrame({'n':[100.,300.],'d':[1.,1.]},index=['a','b'])
    cw=pd.DataFrame({'district_id':['x','y','y'],'deso_id':['a','a','b'],'weight':[.5,.5,1.]})
    assert estimate(f,cw,whole=True).n.isna().all()
    values=estimate(f,cw,count=True)
    assert values.loc['y','n']==350
    assert values.loc['y','d']==1

def test_bad_source_allocation_suppresses_estimate():
    f=pd.DataFrame({'n':[50.],'d':[100.]},index=['a'])
    cw=pd.DataFrame({'district_id':['x'],'deso_id':['a'],'weight':[.8]})
    assert estimate(f,cw).n.isna().all()
