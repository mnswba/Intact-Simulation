"""Locate bundled Intact modules without a developer checkout or system Python."""
import os
from pathlib import Path
import sys
import site
sys.dont_write_bytecode=True

server=Path(__file__).resolve().parents[3]
dependencies=server/'dependencies'
runtime=server/'runtime'
for directory in (dependencies,runtime,runtime/'intact_backend'):
    sys.path.insert(0,str(directory))
site.addsitedir(str(dependencies))
os.environ['INTACT_PYTHON_LIBS']=str(dependencies)
os.environ['INTACT_FREECAD_ROOT']=str(server/'freecad')
os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(server/'browsers')
os.environ.setdefault('INTACT_CODEX_CLI',str(server/'client/bin/codex.exe'))
os.environ.setdefault('INTACT_STATE_DIR',str(Path(os.environ['LOCALAPPDATA'])/'IntactSimulation/projects'))
