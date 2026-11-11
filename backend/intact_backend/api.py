from __future__ import annotations
import asyncio, hmac, os, re
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import Field
from .cad import CadService
from .spec import DesignSpec, StrictModel, Patch, patch_spec, from_legacy, boundary_table, SpecConflict
from .store import Store
from .analysis import evaluate
from .program import ProgramService,ProgramBuildError,SandboxUnavailable
from .generated import generated_spec
from .jobs import Jobs

class SpecRequest(StrictModel):spec:DesignSpec
class AgentRequest(StrictModel):
    prompt:str=Field(min_length=1,max_length=4000)
    spec:DesignSpec|None=None
    design:dict|None=None
    contractVersion:int=1
class PatchRequest(SpecRequest):
    patches:list[Patch]=Field(min_length=1,max_length=30)
    expected_hash:str
class ApprovalRequest(SpecRequest):confirm:bool

state=Path(os.environ.get('INTACT_STATE_DIR',Path.home()/'.local/share/intact-studio'))
store=Store(state/'projects.sqlite3');cad=CadService(state/'geometry');programs=ProgramService(state/'programs');slots=asyncio.Semaphore(2);jobs=Jobs(state/'jobs.sqlite3')
app=FastAPI(title='Intact Simulation · ChatGPT CAD service',version='0.9.0',docs_url='/docs',redoc_url=None)

@app.middleware('http')
async def limits(request:Request,call_next):
    if request.method=='POST':
        try:size=int(request.headers.get('content-length','0'))
        except ValueError:return JSONResponse({'detail':'Invalid content length.'},status_code=400)
        if size>180000:return JSONResponse({'detail':'Request exceeds 180 KB.'},status_code=413)
        # Bound chunked requests too, before the JSON parser sees them.
        data=bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data)>180000:return JSONResponse({'detail':'Request exceeds 180 KB.'},status_code=413)
        request._body=bytes(data)
    response=await call_next(request);response.headers['X-Content-Type-Options']='nosniff';response.headers['Cache-Control']='no-store';return response

async def authorized(request:Request):
    token=os.environ.get('INTACT_SERVICE_TOKEN','')
    if not token:raise HTTPException(503,'Set INTACT_SERVICE_TOKEN before exposing the service.')
    if not hmac.compare_digest(request.headers.get('authorization',''),'Bearer '+token):raise HTTPException(401,'Invalid service credential.')

@app.get('/health')
async def health():return {'status':'ok','agent':'chatgpt','model_configured':False,'external_model_service':False,'freeform_ready':programs.available(),'scope':'ChatGPT tool-driven Python CAD, implicit TPMS and reduced 1D analysis','version':'0.9.0'}

@app.post('/v1/design',dependencies=[Depends(authorized)])
async def design(request:AgentRequest):
    raise HTTPException(409,'Use the Intact Simulation plugin in your ChatGPT conversation. This service does not call a separate AI model.')

@app.post('/v1/spec/patch',dependencies=[Depends(authorized)])
async def patch(request:PatchRequest):
    try:spec=patch_spec(request.spec,request.patches,request.expected_hash)
    except SpecConflict as exc:raise HTTPException(409,str(exc))
    except ValueError as exc:raise HTTPException(422,str(exc))
    store.save('workspace',spec);return {'spec':spec.model_dump(mode='json'),'spec_hash':spec.content_hash()}

@app.post('/v1/spec/approve',dependencies=[Depends(authorized)])
async def approve(request:ApprovalRequest):
    if not request.confirm:raise HTTPException(422,'Explicit confirmation is required.')
    spec=request.spec.model_copy(deep=True);spec.simulation.approved_fingerprint=spec.content_hash()
    return {'spec':spec.model_dump(mode='json'),'boundary_conditions':boundary_table(spec),'spec_hash':spec.content_hash()}

@app.post('/v1/geometry',dependencies=[Depends(authorized)])
async def geometry(request:SpecRequest):
    try:
        async with slots:
            if request.spec.program:
                p=request.spec.program
                report=await asyncio.to_thread(programs.build,p.source,p.parameters)
            else:report=await asyncio.to_thread(cad.build,request.spec)
        return report
    except ValueError as exc:raise HTTPException(422,str(exc))

@app.post('/v1/analysis',dependencies=[Depends(authorized)])
async def analysis(request:SpecRequest):
    spec=request.spec
    if spec.simulation.approved_fingerprint!=spec.content_hash():raise HTTPException(409,'Review and approve the current spec first.')
    cached=store.result(spec.content_hash())
    if cached:return {**cached,'cached':True}
    try:
        async with slots:result=await asyncio.to_thread(evaluate,spec)
        store.save_result(spec.content_hash(),result);return {**result,'cached':False}
    except ValueError as exc:raise HTTPException(422,str(exc))

@app.get('/v1/geometry/{key}/{filename}',dependencies=[Depends(authorized)])
async def artifact(key:str,filename:str):
    if not re.fullmatch('[a-f0-9]{64}',key) or filename not in ('model.step','model.stl','manifest.json','mesh.json','program.py'):raise HTTPException(404,'Artifact not found.')
    root=programs.root if (programs.root/key).is_dir() else cad.root
    path=root/key/filename
    if not path.is_file():raise HTTPException(404,'Artifact not found.')
    return FileResponse(path,filename=filename)

@app.get('/v1/versions',dependencies=[Depends(authorized)])
async def versions():return {'versions':store.history('workspace')}

class ProgramRequest(SpecRequest):
    source:str=Field(min_length=1,max_length=120000)
    parameters:dict[str,float]=Field(default_factory=dict,max_length=150)

@app.post('/v1/jobs',dependencies=[Depends(authorized)])
async def create_design_job(request:AgentRequest):
    raise HTTPException(409,'Use the Intact Simulation plugin in ChatGPT; autonomous model-service jobs have been removed.')

@app.post('/v1/program/jobs',dependencies=[Depends(authorized)])
async def create_program_job(request:ProgramRequest):
    if not programs.available():raise HTTPException(503,'An isolated CAD worker is required for generated Python.')
    from .program_policy import validate_source,validate_parameters
    try:source=validate_source(request.source);parameters=validate_parameters(request.parameters)
    except ValueError as exc:raise HTTPException(422,str(exc))
    async def build(progress,cancel):
        progress({'tool':'execute_cad_program','step':1})
        async with slots:report=await asyncio.to_thread(programs.build,source,parameters,cancel)
        spec=generated_spec(source,parameters,report,request.spec);store.save('workspace',spec)
        return {'status':'built','spec':spec.model_dump(mode='json'),'geometry':report,'message':'CAD program rebuilt and validated.'}
    try:return jobs.create(build)
    except ValueError as exc:raise HTTPException(429,str(exc))

@app.get('/v1/jobs/{key}',dependencies=[Depends(authorized)])
async def job_status(key:str):
    if not re.fullmatch('[a-f0-9]{32}',key):raise HTTPException(404,'Job not found.')
    try:return jobs.get(key)
    except KeyError:raise HTTPException(404,'Job not found.')

@app.delete('/v1/jobs/{key}',dependencies=[Depends(authorized)])
async def cancel_job(key:str):
    try:return jobs.cancel(key)
    except KeyError:raise HTTPException(404,'Job not found.')
