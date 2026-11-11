from copy import deepcopy
import pytest
from pydantic import ValidationError
from intact_backend.spec import DesignSpec,Patch,Part,Parameters,patch_spec,SpecConflict,from_legacy
from intact_backend.analysis import evaluate
from intact_backend.store import Store

def test_atomic_patch_hashes_and_approval(beam):
    beam.simulation.approved_fingerprint=beam.content_hash();old=beam.content_hash()
    updated=patch_spec(beam,[Patch(path='parts.main.params.length',value=200)],old)
    assert beam.parts[0].params.length==180 and updated.parts[0].params.length==200
    assert updated.revision==2 and updated.simulation.approved_fingerprint is None
    assert old!=updated.content_hash()
    with pytest.raises(SpecConflict):patch_spec(updated,[Patch(path='parts.main.name',value='new')],old)
    with pytest.raises(ValueError):patch_spec(beam,[Patch(path='simulation.approved_fingerprint',value=old)])
    with pytest.raises(ValidationError):patch_spec(beam,[Patch(path='parts.main.params.length',value=-1)])
    assert beam.content_hash()==old

def test_unique_ids_and_no_empty_assembly(beam):
    with pytest.raises(ValidationError):patch_spec(beam,[Patch(op='add_part',value=beam.parts[0].model_dump())])
    with pytest.raises(ValidationError):patch_spec(beam,[Patch(op='remove_part',value='main')])

def test_result_hash_ignores_revision_but_includes_load(beam):
    s=beam.model_copy(deep=True);s.revision=100;assert s.content_hash()==beam.content_hash()
    s.simulation.study.force=50;assert s.content_hash()!=beam.content_hash();assert s.geometry_hash()==beam.geometry_hash()

def test_approval_required(beam):
    with pytest.raises(ValueError,match='approve'):evaluate(beam)
    beam.simulation.approved_fingerprint=beam.content_hash();assert evaluate(beam)['scope']=='reduced_1d'

def test_beam_independent_methods_balance_and_scaling(beam):
    a=evaluate(beam,False);assert a['relative_spread']<1e-7
    assert all(c['passed'] for c in a['checks']);assert a['tiers']['C']['status']=='unavailable'
    beam.simulation.study.force*=2;b=evaluate(beam,False);assert b['headline']==pytest.approx(a['headline']*2,rel=1e-7)
    assert a['confidence']=='medium' # explicit material/physics limits cap confidence

def test_fin_conserves_energy_uses_temperature_rise_and_refines(fin):
    a=evaluate(fin,False);assert a['relative_spread']<1e-3
    assert all(c['passed'] for c in a['checks'])
    ambient=fin.simulation.study.ambient;fin.simulation.study.heat*=2;b=evaluate(fin,False)
    assert b['headline']-ambient==pytest.approx(2*(a['headline']-ambient),rel=1e-8)
    assert b['fields'][0]['temperature_c']>b['fields'][-1]['temperature_c']

def test_sqlite_versions_and_results_are_keyed_and_round_trip(tmp_path,beam):
    store=Store(tmp_path/'state.sqlite');store.save('p',beam);store.save('p',beam)
    edited=patch_spec(beam,[Patch(path='parts.main.params.height',value=10)]);store.save('p',edited)
    assert len(store.history('p'))==2;assert store.load('p',beam.content_hash())==beam
    r=evaluate(beam,False);store.save_result(beam.content_hash(),r);assert store.result(beam.content_hash())['headline']==r['headline']
