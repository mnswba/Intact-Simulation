"""Forward-test the installed personal plugin in a fresh signed-in OpenAI local client."""
import json,os,shutil,subprocess,tempfile,time
from pathlib import Path
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/priority23-audit/host';OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path.home()/'.local/share/intact-simulation/audit-host'
with tempfile.TemporaryDirectory(prefix='intact-plugin-host-') as folder:
 output=OUT/'final.txt'
 cmd=[shutil.which('codex'),'exec','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--color','never','--json','-C',folder,'-o',str(output)]
 for feature in ('shell_tool','apps','browser_use','computer_use','multi_agent','hooks','shell_snapshot'):cmd+=['--disable',feature]
 cmd+=['-c','web_search="disabled"','-c','project_doc_max_bytes=0','-c','approval_policy="never"','-']
 prompt='Use Intact Simulation to create a native rectangular test domain 20 mm in X, 10 mm in Y, 10 mm in Z, named Priority 2/3 live audit. Run a real 3D linear-elastic study: clamp the minimum-X end, distribute a total 1 N force in +X at the maximum-X end, Young modulus 70 GPa and Poisson ratio 0.3. Use 4 mm mesh size and compare a finer mesh at 15 percent relative convergence tolerance. Report displacement in mm, residual, force balance, convergence and the solver scope. Compare the displacement to the axial formula FL/(EA). Inspect the actual CAD snapshot and give the viewer and VTU result links. Then create a separate 4 mm cube gyroid distance-offset lattice with cell size 8 mm, target thickness 1.6 mm and 24 samples per cell. Measure its exported mesh quality and finite wall samples, clearly distinguish target thickness from measurements and uncertainty, inspect its snapshot, and provide a printable STL link. Use Intact tools only. Do not claim turbulent CFD, exact smooth TPMS STEP or manufacturing certification.'
 env={k:v for k,v in os.environ.items() if k not in ('CODEX_THREAD_ID','CODEX_TURN_ID')};env['INTACT_STATE_DIR']=str(ROOT)
 started=time.monotonic()
 with (OUT/'events.jsonl').open('w') as stdout,(OUT/'stderr.log').open('w') as stderr:
  p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,env=env,start_new_session=True,text=True);
  try:p.communicate(prompt,timeout=300)
  except subprocess.TimeoutExpired:
   import signal
   os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=15);raise
 events=[]
 for line in (OUT/'events.jsonl').read_text().splitlines():
  try:events.append(json.loads(line))
  except ValueError:pass
 names=[]
 for event in events:
  item=event.get('item',{})
  if 'tool' in item:names.append(str(item['tool']))
  elif item.get('type')=='mcp_tool_call':names.append(str(item.get('tool')))
 report={'exit_code':p.returncode,'elapsed_seconds':round(time.monotonic()-started,2),'tool_names':names,'final':output.read_text() if output.exists() else '', 'client':'Codex local client with personal plugin marketplace; Windows desktop GUI not controlled'}
 assert p.returncode==0,report
 assert all(t in names for t in ('build_model','run_3d_simulation','build_lattice_mm','measure_mesh_quality','snapshot_model')),names
 (OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
