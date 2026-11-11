"""Exercise the installed plugin through the official MCP client, not a direct engine call.
Run with the installed runtime's Python. Output artifacts stay under outputs/plugin-audit.
"""
import asyncio, ast, base64, io, json, math, os, sys, zipfile
from pathlib import Path
from urllib.request import urlopen
from mcp import Client,StdioServerParameters

REPO=Path(__file__).resolve().parents[1]
OUT=REPO/'outputs/plugin-audit';OUT.mkdir(parents=True,exist_ok=True)
CASES={
'flange':('''import build123d as bd
import math
def build(params):
    d=params['diameter'];t=params['thickness']
    body=bd.Cylinder(d/2,t)-bd.Cylinder(params['bore']/2,t+2)
    for i in range(6):
        a=math.radians(i*60)
        body-=bd.Pos(30*math.cos(a),30*math.sin(a),0)*bd.Cylinder(3,t+2)
    cover=bd.Pos(0,0,18)*(bd.Cylinder(d/2,3)-bd.Cylinder(params['bore']/2,5))
    return {'flange':body,'cover':cover}
''',{'diameter':80,'thickness':8,'bore':24}),
'bracket':('''import build123d as bd
def build(params):
    l=params['length'];w=params['width'];h=params['height'];t=params['thickness']
    align=(bd.Align.MIN,bd.Align.MIN,bd.Align.MIN)
    body=bd.Box(l,w,t,align=align)+bd.Box(t,w,h,align=align)
    body=bd.fillet(body.edges().filter_by(bd.Axis.Y),radius=1)
    body-=bd.Pos(l*0.65,w/2,-1)*bd.Cylinder(3,t+2,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    body-=bd.Pos(-1,w/2,h*0.65)*bd.Rot(0,90,0)*bd.Cylinder(3,t+2,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    return {'bracket':body}
''',{'length':60,'width':35,'height':40,'thickness':5}),
'revolved_pulley':('''import build123d as bd
def build(params):
    r=params['radius'];h=params['height']
    with bd.BuildPart() as body:
        with bd.BuildSketch(bd.Plane.XZ):
            bd.Polygon((0,0),(r,0),(r,3),(r-4,5),(r-4,h-5),(r,h-3),(r,h),(0,h),align=None)
        bd.revolve(axis=bd.Axis.Z)
    return {'pulley':body.part-bd.Cylinder(6,h+2,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))}
''',{'radius':20,'height':20}),
'lofted_duct':('''import build123d as bd
def build(params):
    r0=params['base_radius'];r1=params['top_radius'];h=params['height'];w=params['wall']
    outer=bd.loft([bd.Plane.XY*bd.Circle(r0),bd.Plane.XY.offset(h)*bd.Circle(r1)])
    inner=bd.loft([bd.Plane.XY*bd.Circle(r0-w),bd.Plane.XY.offset(h)*bd.Circle(r1-w)])
    return {'duct':outer-inner}
''',{'base_radius':30,'top_radius':18,'height':50,'wall':2}),
'swept_elbow':('''import build123d as bd
def build(params):
    r=params['bend_radius']
    path=bd.Plane.XZ*bd.CenterArc((0,0),r,0,90)
    start=bd.Plane(origin=(r,0,0),z_dir=(0,0,1))
    outer=bd.sweep(start*bd.Circle(params['outer_radius']),path)
    inner=bd.sweep(start*bd.Circle(params['inner_radius']),path)
    return {'elbow':outer-inner}
''',{'bend_radius':40,'outer_radius':5,'inner_radius':3.5})
}

def data(result):
    if result.is_error:raise AssertionError('\n'.join(c.text for c in result.content if hasattr(c,'text')))
    return result.structured_content

async def main():
    manifest=Path.home()/'.codex/plugins/intact-simulation/.mcp.json'
    server=json.loads(manifest.read_text())['mcpServers']['intact']
    params=StdioServerParameters(command=server['command'],args=server['args'])
    report={'models':{},'checks':[]}
    async with Client(params,read_timeout_seconds=110) as client:
        status=data(await client.call_tool('status'));assert status['cad_ready'] and status['version']=='0.8.0'
        report['status']=status;report['checks'].append('installed runtime ready')
        for name,(source,parameters) in CASES.items():
            result=data(await client.call_tool('build_model',{'source':source,'parameters':parameters,'name':'Plugin audit · '+name}))
            key=result['model_id'];report['models'][name]=result
            measured=data(await client.call_tool('measure_model',{'model_id':key}))
            assert all(p['volume_mm3']>0 and p['solid_count']>=1 for p in measured['parts'])
            if name=='flange':
                expected=(math.pi*(40**2-12**2)-6*math.pi*3**2)*8
                assert math.isclose(measured['parts'][0]['volume_mm3'],expected,rel_tol=1e-6)
                assert measured['parts'][0]['bounds']['length']==80
            if name=='swept_elbow':
                expected=math.pi*(5**2-3.5**2)*(math.pi/2*40)
                assert math.isclose(measured['parts'][0]['volume_mm3'],expected,rel_tol=1e-5)
            for kind,url in result['downloads'].items():
                body=urlopen(url,timeout=10).read();(OUT/(name+'.'+{'step':'step','stl':'stl','glb':'glb','3mf':'3mf','python':'py','project':'json'}[kind])).write_bytes(body)
                if kind=='glb':assert body[:4]==b'glTF'
                if kind=='3mf':
                    with zipfile.ZipFile(io.BytesIO(body)) as z:assert any(p.endswith('.model') for p in z.namelist())
                if kind=='step':
                    assert b'ISO-10303-21' in body[:80]
                    import build123d as bd
                    roundtrip=bd.import_step(OUT/(name+'.step'))
                    assert roundtrip.is_valid and len(roundtrip.solids())==len(measured['parts'])
                    assert math.isclose(roundtrip.volume,sum(p['volume_mm3'] for p in measured['parts']),rel_tol=1e-6)
                if kind=='python':ast.parse(body.decode())
                if kind=='project':assert json.loads(body)['spec']['program']['source']==source
            report['checks'].append(name+' built, measured and exported all formats');print('PASS '+name,flush=True)
        flange=report['models']['flange'];key=flange['model_id']
        data(await client.call_tool('set_appearance',{'model_id':key,'part_id':'flange','color':'#df873c'}))
        updated=data(await client.call_tool('update_parameters',{'model_id':key,'parameters':{'diameter':90}}))
        saved=data(await client.call_tool('get_model',{'model_id':key}));revision=saved['spec']['revision']
        assert saved['name']=='Plugin audit · flange' and saved['spec']['parts'][0]['color']=='#df873c'
        assert saved['spec']['parts'][0]['params']['length']==90
        bad=await client.call_tool('update_parameters',{'model_id':key,'parameters':{'diameter':0}});assert bad.is_error
        assert data(await client.call_tool('get_model',{'model_id':key}))['spec']['revision']==revision
        restored=data(await client.call_tool('restore_revision',{'model_id':key,'revision':1}));assert restored['revision']>revision
        # Test cancellation while the same real server is handling a Python build.
        task=asyncio.create_task(client.call_tool('build_model',{'source':'def build(params):\n    while True:\n        pass','parameters':{},'model_id':key}))
        await asyncio.sleep(2);task.cancel()
        try:await task
        except asyncio.CancelledError:pass
        await asyncio.sleep(1)
        assert data(await client.call_tool('get_model',{'model_id':key}))['spec']['revision']==restored['revision']
        report['checks'].append('parameter edits, saved colors, failed-edit preservation, restoration and cancellation')
        imported=data(await client.call_tool('import_project',{'path':str(OUT/'bracket.json')}));assert imported['model_id']!=report['models']['bracket']['model_id']
        thermal=data(await client.call_tool('analyze_reference',{'kind':'fin','length':80,'width':40,'height':3,'material':'copper','study':{'type':'thermal','heat':5,'ambient':25,'convection':15,'nodes':41},'approved':True}))
        assert thermal['scope']=='reduced_1d' and len(thermal['fields'])==41
        assert all(c['passed'] for c in thermal['checks']);report['analysis']=thermal
        report['checks'].append('project import rebuild and actual thermal reference results')
        # Verify model-readable image results without changing the user's saved camera.
        for name,view in [('flange','iso'),('bracket','iso'),('swept_elbow','left')]:
            key=report['models'][name]['model_id']
            before=data(await client.call_tool('get_model',{'model_id':key}))
            result=await client.call_tool('snapshot_model',{'model_id':key,'view':view})
            assert not result.is_error,result
            images=[c for c in result.content if c.type=='image'];assert images
            png=base64.b64decode(images[0].data);assert png[:8]==b'\x89PNG\r\n\x1a\n'
            (OUT/('mcp-snapshot-'+name+'.png')).write_bytes(png)
            after=data(await client.call_tool('get_model',{'model_id':key}));assert before['view']==after['view']
        repair=await client.call_tool('build_model',{'model_id':flange['model_id'],'source':'def build(params):\n    raise ValueError("repair detail exposed")','parameters':{}})
        assert repair.is_error and any('repair detail exposed' in c.text for c in repair.content if hasattr(c,'text'))
        report['checks'].append('agent PNG snapshots, saved-view preservation and actionable CAD repair errors')
    for model in report['models'].values():assert urlopen(model['viewer_url'],timeout=5).status==200
    report['checks'].append('viewer URLs remain available after the MCP connection closes')
    (OUT/'report.json').write_text(json.dumps(report,indent=2));print('Installed plugin checks passed. Report: '+str(OUT/'report.json'))

if __name__=='__main__':asyncio.run(main())
