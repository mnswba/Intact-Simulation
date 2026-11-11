import pytest
from intact_backend.spec import from_legacy, Part,Parameters
from intact_backend.cad import build_in_process,CadService
@pytest.mark.parametrize('kind,L,W,H',[('beam',180,30,8),('fin',80,40,3),('plate',100,70,6),('heatsink',100,80,35),('box_shell',160,100,50)])
def test_real_kernel_solid_dimensions_faces_and_step_export(tmp_path,kind,L,W,H):
    spec=from_legacy(dict(name=kind,kind=kind,length=L,width=W,height=H,holeDiameter=6,finCount=9,material='aluminum'))
    report=build_in_process(spec,tmp_path)
    assert report['valid'] and report['parts'][0]['solid_count']==1
    assert report['parts'][0]['named_faces']['base']['area_mm2']>0
    assert report['parts'][0]['volume_mm3']>0
    assert (tmp_path/'model.step').stat().st_size>1000
    if kind=='box_shell':assert 'pcb_mount' in report['parts'][0]['named_faces']

def test_interference_is_rejected(tmp_path,beam):
    other=beam.parts[0].model_copy(deep=True);other.id='second';beam.parts.append(other)
    with pytest.raises(ValueError,match='interference'):build_in_process(beam,tmp_path)

def test_deterministic_subprocess_build_and_geometry_cache(tmp_path,beam):
    service=CadService(tmp_path);first=service.build(beam);second=service.build(beam)
    assert not first['cached'] and second['cached']
    beam.simulation.study.force=50;assert service.build(beam)['cached']
