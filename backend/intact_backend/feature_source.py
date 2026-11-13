# SPDX-License-Identifier: Apache-2.0
"""Standalone FreeCAD Python export for structured feature projects."""
from pathlib import Path
import re
def executable_feature_source(engineering):
    worker=Path(__file__).with_name('freecad_worker.py').read_text()
    worker=worker.replace('from worker_context import resource,worker_path\n','')
    worker=re.sub(r"worker_path\((['\"])([^'\"]*)\1\)",lambda match:repr(match[2]),worker)
    # The exported program is trusted adapter source plus data, not model Python.
    worker=worker.replace('import json,math,resource,sys,traceback','import json,math,sys,traceback')
    worker='\n'.join(line for line in worker.splitlines() if not line.startswith('resource.setrlimit'))
    worker=worker.replace("json.loads(Path('/input/request.json').read_text())", "{'mode':'rebuild','engineering':ENGINEERING}")
    worker=worker.replace("'/work/result.step'", "str(Path.cwd()/'model.step')").replace("'/work/design.FCStd'", "str(Path.cwd()/'design.FCStd')").replace("'/work/report.json'", "str(Path.cwd()/'report.json')").replace("'/work/error.json'", "str(Path.cwd()/'error.json')")
    return '# Run with FreeCAD 1.1.4 Python. Dimensions are millimeters.\n# Edit PARAMETERS, then run this script to rebuild all sketches/features.\nPARAMETERS = '+repr(engineering['parameters'])+'\nENGINEERING = '+repr(engineering)+"\nENGINEERING['parameters'] = PARAMETERS\n"+worker+'\n'
