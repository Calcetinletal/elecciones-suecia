import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_2026 import reporting_counts

def test_reported_collection_units_are_not_territorial_districts():
    data={'antalValdistriktRaknade':2,'antalValdistriktSomSkaRaknas':3,'valdistrikt':[
        {'valdistriktskod':'a','valdistriktstyp':'valdistrikt','rostfordelning':{'counted':True}},
        {'valdistriktskod':'b','valdistriktstyp':'uppsamlingsdistrikt','rostfordelning':{'counted':True}},
        {'valdistriktskod':'c','valdistriktstyp':'uppsamlingsdistrikt','rostfordelning':None}]}
    counts=reporting_counts(data)
    assert counts['reported_unit_count']==2
    assert counts['reported_district_count']==1
    assert counts['reported_non_geographic_count']==1
    assert counts['pending_non_geographic_count']==1
    assert counts['pending_district_count']==0
    data['antalValdistriktRaknade']=1
    with pytest.raises(ValueError,match='count mismatch'):reporting_counts(data)
