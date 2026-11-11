"""Run a downloaded CAD Python file inside a network/filesystem-isolated test worker."""
import os,signal,subprocess,sys,tempfile
from pathlib import Path

def verify_python_export(path):
    from intact_backend.program import ProgramService
    import build123d as bd
    path=Path(path).resolve()
    with tempfile.TemporaryDirectory(prefix='intact-export-check-') as tmp:
        root=Path(tmp);out=root/'output';out.mkdir();service=ProgramService(root/'locks')
        runtime=Path(sys.base_prefix).resolve();venv=Path(sys.prefix).resolve()
        cmd=[service.binary,'--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv']
        for mount in dict.fromkeys(['/usr','/lib','/lib64',str(runtime),str(Path(sys.base_prefix)),str(Path(os.readlink(venv/'bin/python')).parent.parent),str(venv)]):cmd+=['--ro-bind',mount,mount]
        if Path('/etc/ld.so.cache').exists():cmd+=['--ro-bind','/etc/ld.so.cache','/etc/ld.so.cache']
        cmd+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/home/cad','--ro-bind',str(path.parent),'/input','--bind',str(out),'/work','--chdir','/work']
        for key,value in {'PATH':'/usr/bin:/bin','HOME':'/home/cad','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','PYTHONNOUSERSITE':'1'}.items():cmd+=['--setenv',key,value]
        code='import resource,runpy;resource.setrlimit(resource.RLIMIT_CPU,(35,35));resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2));runpy.run_path('+repr('/input/'+path.name)+',run_name="__main__")'
        cmd +=[str(venv/'bin/python'),'-c',code]
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        try:
            stdout,stderr=process.communicate(timeout=60)
            if process.returncode:raise AssertionError(stderr.decode(errors='replace')[-3000:])
        finally:
            if process.poll() is None:os.killpg(process.pid,signal.SIGKILL);process.wait()
        for name in ('model.stl','model.glb','model.3mf'):assert (out/name).stat().st_size>40
        if not (out/'model.step').exists():
            import trimesh,zipfile,xml.etree.ElementTree as ET
            mesh=trimesh.load(out/'model.stl',force='mesh',process=True)
            with zipfile.ZipFile(out/'model.3mf') as archive:
                root=ET.fromstring(archive.read('3D/3dmodel.model'));ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
                colors={b.get('name'):tuple(int(b.get('displaycolor')[i:i+2],16) for i in (1,3,5)) for b in root.findall('.//m:base',ns)}
            return {'valid':mesh.is_volume and mesh.is_watertight,'volume':float(mesh.volume),'solid_count':int(mesh.body_count),'labels':list(colors),'colors':colors,'mesh_only':True}
        shape=bd.import_step(out/'model.step')
        return {'valid':shape.is_valid,'volume':shape.volume,'solid_count':len(shape.solids()),'labels':[c.label for c in shape.children],'colors':{c.label:tuple(round(v*255) for v in tuple(c.color)[:3]) if c.color else None for c in shape.children}}
