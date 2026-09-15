from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pandas as pd
import numpy as np
import pytest
from build_district_income import estimate_income

def sources():
    return pd.DataFrame({'deso_id':['a','b'],'income_persons':[100.,900.],'income_mean_tkr':[100.,300.]})
def crosswalk():
    return pd.DataFrame({'deso_id':['a','b'],'district_id':['d','d'],'weight':[.5,.1]})
def test_income_uses_own_person_counts_and_converts_tkr_to_sek():
    result=estimate_income(sources(),crosswalk()).loc['d']
    assert result.income_population==140
    assert result.income_total_sek==32000000
    assert result.mean_net_income==pytest.approx(32000000/140)
    assert result.mean_net_income!=pytest.approx((100000*.5+300000*.1)/.6)
def test_missing_contributor_suppresses_estimate_without_renormalising():
    frame=sources();frame.loc[1,'income_mean_tkr']=np.nan
    result=estimate_income(frame,crosswalk()).loc['d']
    assert not result.income_complete
    assert pd.isna(result.mean_net_income) and pd.isna(result.income_total_sek) and pd.isna(result.income_population)
def test_zero_income_is_valid_but_zero_people_is_not():
    frame=sources();frame.income_mean_tkr=0.
    assert estimate_income(frame,crosswalk()).loc['d','mean_net_income']==0
    frame.loc[1,'income_persons']=0
    assert not estimate_income(frame,crosswalk()).loc['d','income_complete']
def test_zero_weight_missing_source_does_not_invalidate_district():
    cw=pd.concat([crosswalk(),pd.DataFrame({'deso_id':['missing'],'district_id':['d'],'weight':[0.]})])
    assert estimate_income(sources(),cw).loc['d','income_complete']
def test_invalid_and_duplicate_sources_are_rejected():
    with pytest.raises(ValueError,match='Duplicate'):estimate_income(pd.concat([sources(),sources()]),crosswalk())
    cw=crosswalk();cw.loc[0,'weight']=-1
    with pytest.raises(ValueError,match='weights'):estimate_income(sources(),cw)
