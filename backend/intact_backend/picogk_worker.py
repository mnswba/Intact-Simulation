"""Trusted bounded PicoGK bridge, executed inside the existing no-network sandbox."""
import json,os,resource,subprocess,sys,traceback
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_CPU,(150,150));resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
try:
 env={**os.environ,'DOTNET_ROOT':'/pico-dotnet','DOTNET_CLI_TELEMETRY_OPTOUT':'1','DOTNET_EnableDiagnostics':'0','DOTNET_EnableWriteXorExecute':'0','DOTNET_GCHeapHardLimit':'40000000','DOTNET_SKIP_FIRST_TIME_EXPERIENCE':'1','HOME':'/home/cad'}
 subprocess.run(['/pico-dotnet/dotnet','/pico-bridge/Intact.PicoGK.dll','/input/request.json','/work/result.stl'],env=env,check=True,timeout=140,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
 import trimesh
 mesh=trimesh.load('/work/result.stl',force='mesh',process=True)
 if not mesh.is_watertight or mesh.volume<=0 or len(mesh.faces)>600000:raise ValueError('PicoGK mesh is not closed/positive or exceeds 600,000 faces. Adjust voxel size.')
 s=json.loads(Path('/input/request.json').read_text());report={'kind':'picogk_tpms','engine':'PicoGK','package_version':'2.4.0-alpha04','voxel_mm':s['voxel_mm'],'volume_mm3':float(mesh.volume),'triangles':len(mesh.faces),'watertight':True,'scope':'PicoGK implicit voxel shell, local-gradient distance approximation and nominal wall thickness. No exact uniform wall, smooth STEP or certified tolerance claim. Linux runtime is a pinned prerelease.','settings':s}
 Path('/work/report.json').write_text(json.dumps(report,allow_nan=False))
except BaseException as exc:Path('/work/error.json').write_text(json.dumps({'error':str(exc)+' '+str(getattr(exc,'stderr',''))[-1500:],'traceback':traceback.format_exc()[-2000:]}));sys.exit(1)
