"""Headless result auditing; no numerical estimates or silent BC substitutions."""
import math


def audit_result(result,geometry):
    checks=[]
    def check(name,passed,**facts):checks.append({'check':name,'passed':bool(passed),**facts})
    check('geometry gate',geometry.get('status')=='passed')
    positions=result.get('positions_mm',[]);values=result.get('values',[])
    check('finite nonempty result field',bool(values) and len(values)==len(positions) and all(isinstance(v,(float,int)) and math.isfinite(v) for v in values))
    for field,field_values in result.get('fields',{}).items():check('finite field '+field,len(field_values)==len(positions) and all(isinstance(v,(float,int)) and math.isfinite(v) for v in field_values))
    check('finite coordinates',bool(positions) and all(isinstance(p,list) and len(p)==3 and all(isinstance(v,(float,int)) and math.isfinite(v) for v in p) for p in positions))
    check('solver residual',math.isfinite(result.get('relative_residual',float('inf'))) and result['relative_residual']<=1e-6,value=result.get('relative_residual'),limit=1e-6)
    check('conservation / reaction balance',math.isfinite(result.get('relative_balance_error',float('inf'))) and result['relative_balance_error']<=1e-5,value=result.get('relative_balance_error'),limit=1e-5)
    if not all(c['passed'] for c in checks):raise ValueError('Headless simulation audit rejected invalid fields or failed numerical checks. No successful result was published.')
    verification=[{'check':'mesh refinement','passed':result.get('convergence',{}).get('passed',False)},{'check':'supported physical regime','passed':result.get('regime_valid',True)}]
    if result.get('kind')=='structural':verification.append({'check':'stress refinement','passed':result.get('stress_convergence',{}).get('passed',False)})
    design=geometry.get('design_verification',{});design_status=design.get('status','not_evaluated') if isinstance(design,dict) else 'not_evaluated'
    return {'mode':'headless','status':'passed' if all(c['passed'] for c in verification) and design_status not in ('failed','unverified','not_evaluated') else 'needs_review','geometry_status':geometry.get('status'),'design_requirements':design_status,'numerical_checks':checks,'verification_checks':verification,'scope':'Geometry, finite solver output, residual, conservation and reported refinement/regime checks. Boundary/material assumptions and physical applicability still require engineering review.'}
