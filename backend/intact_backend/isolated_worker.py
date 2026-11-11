# SPDX-License-Identifier: Apache-2.0
"""Run trusted geometry workers with private input/output mounts and no network."""
import json,os,signal,subprocess,time
from pathlib import Path

def run_worker(service,script,input_dir,output_dir,python=None,mounts=None,env=None,cancel_event=None,timeout=120):
    import sys
    if not service.available():raise ValueError('A working bubblewrap sandbox is required.')
    python=Path(python or sys.executable);script=Path(script).resolve();input_dir=Path(input_dir).resolve();output_dir=Path(output_dir).resolve()
    if mounts is None:mounts=[str(Path(sys.base_prefix)),str(Path(sys.base_prefix).resolve()),str(Path(sys.prefix).resolve()),str(Path(os.readlink(Path(sys.prefix)/'bin/python')).parent.parent)]
    cmd=[service.binary,'--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv']
    for p in dict.fromkeys(['/usr','/lib','/lib64',*map(str,mounts)]):cmd+=['--ro-bind',p,p]
    if Path('/etc/ld.so.cache').exists():cmd+=['--ro-bind','/etc/ld.so.cache','/etc/ld.so.cache']
    cmd+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/home/cad','--ro-bind',str(input_dir),'/input','--bind',str(output_dir),'/work','--ro-bind',str(script),'/worker.py','--chdir','/work']
    # FreeCAD uses getpwuid as well as HOME. Supply a synthetic identity rather
    # than exposing the host passwd database or the user's actual home.
    (input_dir/'worker-passwd').write_text(f'cad:x:{os.getuid()}:{os.getgid()}:CAD:/home/cad:/bin/sh\n')
    (input_dir/'worker-group').write_text(f'cad:x:{os.getgid()}:\n')
    cmd+=['--ro-bind',str(input_dir/'worker-passwd'),'/etc/passwd','--ro-bind',str(input_dir/'worker-group'),'/etc/group']
    settings={'PATH':'/usr/bin:/bin','HOME':'/home/cad','USER':'cad','LOGNAME':'cad','PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','QT_QPA_PLATFORM':'offscreen',**(env or {})}
    for k,v in settings.items():cmd+=['--setenv',k,str(v)]
    cmd += [str(python),'/worker.py']
    log=output_dir/'worker.log'
    with log.open('wb') as stream:
        process=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,env={'PATH':'/usr/bin:/bin'})
        deadline=time.monotonic()+timeout
        try:
            while process.poll() is None:
                if cancel_event and cancel_event.is_set():raise ValueError('Operation cancelled; saved design preserved.')
                if time.monotonic()>deadline:raise ValueError('Geometry worker timed out; saved design preserved.')
                time.sleep(.05)
        finally:
            if process.poll() is None:os.killpg(process.pid,signal.SIGKILL);process.wait()
    if process.returncode:
        error=output_dir/'error.json'
        detail=json.loads(error.read_text()).get('error','') if error.exists() else log.read_text(errors='replace')[-3000:]
        raise ValueError('Isolated geometry worker failed: '+str(detail)[:3500])
    path=output_dir/'report.json'
    if not path.is_file() or path.stat().st_size>16*1024**2:raise ValueError('Geometry worker did not return a bounded report.')
    return json.loads(path.read_text())
