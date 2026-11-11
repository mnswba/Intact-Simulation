import pytest
from intact_backend.spec import from_legacy
@pytest.fixture
def beam():return from_legacy({'name':'Beam','kind':'beam','length':180,'width':30,'height':8,'holeDiameter':6,'finCount':9,'material':'aluminum'})
@pytest.fixture
def fin():return from_legacy({'name':'Cooling fin','kind':'fin','length':80,'width':40,'height':3,'holeDiameter':6,'finCount':9,'material':'aluminum'},{'type':'thermal'})
