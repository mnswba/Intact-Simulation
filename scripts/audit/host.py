"""Forward-test the installed personal plugin in a fresh signed-in OpenAI local client."""
import json,os,shutil,subprocess,tempfile,time
from pathlib import Path
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/50-model-audit/host';OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path.home()/'.local/share/intact-simulation/audit-host'
with tempfile.TemporaryDirectory(prefix='intact-plugin-host-') as folder:
 output=OUT/'final.txt'
 cmd=[shutil.which('codex'),'exec','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--color','never','--json','-C',folder,'-o',str(output)]
 for feature in ('shell_tool','apps','browser_use','computer_use','multi_agent','hooks','shell_snapshot'):cmd+=['--disable',feature]
 cmd+=['-c','web_search="disabled"','-c','project_doc_max_bytes=0','-c','approval_policy="never"','-']
 prompt='Use the installed Intact Simulation plugin to create a circular mounting flange: 80 mm outside diameter, 24 mm central bore, 8 mm thickness, and six 6 mm bolt holes on a 60 mm bolt circle. Make these dimensions editable. Show me the finished model and provide STEP and STL download links.'
 env={k:v for k,v in os.environ.items() if k not in ('CODEX_THREAD_ID','CODEX_TURN_ID')};env['INTACT_STATE_DIR']=str(ROOT)
 started=time.monotonic()
 with (OUT/'events.jsonl').open('w') as stdout,(OUT/'stderr.log').open('w') as stderr:
  p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,env=env,start_new_session=True,text=True);p.communicate(prompt,timeout=240)
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
 (OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
