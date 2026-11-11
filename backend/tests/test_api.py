import importlib
import pytest
from fastapi.testclient import TestClient
@pytest.fixture
def api_client(tmp_path,monkeypatch):
    monkeypatch.setenv('INTACT_STATE_DIR',str(tmp_path));monkeypatch.setenv('INTACT_SERVICE_TOKEN','unit-test-token')
    monkeypatch.delenv('INTACT_LLM_MODEL',raising=False)
    import intact_backend.api as module
    module=importlib.reload(module)
    with TestClient(module.app) as client:yield client

def test_health_does_not_claim_a_live_model(api_client):
    r=api_client.get('/health');assert r.status_code==200 and r.json()['agent']=='chatgpt'
    assert not r.json()['model_configured']

def test_authentication_and_unconfigured_agent(api_client,beam):
    assert api_client.post('/v1/design',json={'prompt':'beam','spec':beam.model_dump()}).status_code==401
    r=api_client.post('/v1/design',headers={'Authorization':'Bearer unit-test-token'},json={'prompt':'beam','spec':beam.model_dump()})
    assert r.status_code==409 and 'ChatGPT' in r.json()['detail']

def test_explicit_approval_and_stale_results(api_client,beam):
    headers={'Authorization':'Bearer unit-test-token'};body={'spec':beam.model_dump()}
    assert api_client.post('/v1/analysis',headers=headers,json=body).status_code==409
    approval=api_client.post('/v1/spec/approve',headers=headers,json={**body,'confirm':True});assert approval.status_code==200
    approved=approval.json()['spec'];run=api_client.post('/v1/analysis',headers=headers,json={'spec':approved})
    assert run.status_code==200 and run.json()['scope']=='reduced_1d'
    cached=api_client.post('/v1/analysis',headers=headers,json={'spec':approved});assert cached.json()['cached']
    approved['simulation']['study']['force']=50
    assert api_client.post('/v1/analysis',headers=headers,json={'spec':approved}).status_code==409

def test_body_and_artifact_path_limits(api_client):
    headers={'Authorization':'Bearer unit-test-token'}
    assert api_client.post('/v1/design',headers=headers,content='x'*180001).status_code==413
    assert api_client.get('/v1/geometry/'+'a'*64+'/secret.txt',headers=headers).status_code==404
