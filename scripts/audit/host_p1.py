"""Forward-test the installed personal plugin in a fresh signed-in OpenAI local client."""
import json,os,shutil,subprocess,tempfile,time
from pathlib import Path
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/priority1-audit/host';OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path.home()/'.local/share/intact-simulation/audit-host'
with tempfile.TemporaryDirectory(prefix='intact-plugin-host-') as folder:
 output=OUT/'final.txt'
 cmd=[shutil.which('codex'),'exec','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--color','never','--json','-C',folder,'-o',str(output)]
 for feature in ('shell_tool','apps','browser_use','computer_use','multi_agent','hooks','shell_snapshot'):cmd+=['--disable',feature]
 cmd+=['-c','web_search="disabled"','-c','project_doc_max_bytes=0','-c','approval_policy="never"','-']
 prompt='Use Intact Simulation to design a parametric 40 mm diameter, 8 mm thick disk with two 6 mm through mounting holes at X=-10 and X=10 mm, Y=0. I need a fully constrained editable outline sketch, named feature history and saved checks for these dimensions and hole locations. Then change the hole diameter to 8 mm using its parameter, update the requested acceptance dimensions, rebuild and verify the actual result. Show the top and isometric views, and provide STEP and editable project links. Use Intact tools only, and report any verification failures honestly. Call this model Priority 1 live audit disk.'
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
 assert all(t in names for t in ('create_sketch','solve_sketch','edit_feature_tree','update_parameters','verify_design','snapshot_model','export_model')),names
 (OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
