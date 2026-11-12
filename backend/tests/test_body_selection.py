import pytest
from intact_backend.projects import ProjectService
from intact_backend.body_selection import bodies
from intact_backend.edit_requests import EditRequests

def test_native_solids_are_distinct_and_referenceable_without_revisions(tmp_path):
 s=ProjectService(tmp_path);r=s.build('import build123d as b\ndef build(params):\n return {"pair":b.Compound(children=[b.Pos(-12,0,0)*b.Box(10,10,10),b.Pos(12,0,0)*b.Box(10,10,10)])}',{});before=s.load(r['model_id']);result=bodies(s,r);assert len(result['bodies'])==2
 a,b=result['bodies'];assert set(a['face_refs']).isdisjoint(b['face_refs']);assert len(a['face_refs'])==len(b['face_refs'])==6;assert a['volume_mm3']==pytest.approx(1000)
 context=EditRequests(s).resolve(r['model_id'],[a['ref']],r['spec']['revision'],r['spec']['program']['artifact_id']);assert context['references'][0]['kind']=='body';assert bodies(s,r)==result;assert s.load(r['model_id'])==before

def test_hollow_solid_is_one_body_with_inner_faces(tmp_path):
 s=ProjectService(tmp_path);r=s.build('import build123d as b\ndef build(params):\n return {"shell":b.Box(20,20,20)-b.Box(10,10,10)}',{});result=bodies(s,r);assert len(result['bodies'])==1;assert len(result['bodies'][0]['face_refs'])==12;assert result['bodies'][0]['volume_mm3']==pytest.approx(7000)


def test_selected_part_body_inspection_ignores_unrelated_ambiguous_solids(tmp_path):
 s=ProjectService(tmp_path);r=s.build('import build123d as b\ndef build(params):\n return {"good":b.Pos(30,0,0)*b.Box(10,10,10),"ambiguous":b.Compound(children=[b.Box(10,10,10),b.Box(10,10,10)])}',{})
 result=bodies(s,r,'good');assert len(result['bodies'])==1;assert result['bodies'][0]['part_id']=='good'
