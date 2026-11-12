import pytest
from intact_backend.simulation_audit import audit_result

def result():return {'kind':'thermal','positions_mm':[[0,0,0],[1,0,0]],'values':[300.,350.],'relative_residual':1e-10,'relative_balance_error':1e-10,'convergence':{'passed':True}}
def test_actual_numerics_required_for_audit_pass():
 r=result();assert audit_result(r,{'status':'passed','design_verification':{'status':'not_specified'}})['status']=='passed'
 for patch in [{'values':[float('nan'),350.]},{'relative_residual':.001},{'relative_balance_error':.001},{'positions_mm':[]}]:
  with pytest.raises(ValueError):audit_result({**r,**patch},{'status':'passed'})
def test_missing_refinement_does_not_become_verified():
 r=result();r['convergence']={'passed':False};assert audit_result(r,{'status':'passed'})['status']=='needs_review'
 r=result();r.update(kind='structural',stress_convergence={'passed':False});assert audit_result(r,{'status':'passed'})['status']=='needs_review'
