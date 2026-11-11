"""Forward-test the installed personal plugin in a fresh signed-in OpenAI local client."""
import json,os,shutil,subprocess,tempfile,time
from pathlib import Path
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/0.9-audit/host';OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path.home()/'.local/share/intact-simulation/audit-host'
with tempfile.TemporaryDirectory(prefix='intact-plugin-host-') as folder:
 output=OUT/'final.txt'
 cmd=[shutil.which('codex'),'exec','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--color','never','--json','-C',folder,'-o',str(output)]
 for feature in ('shell_tool','apps','browser_use','computer_use','multi_agent','hooks','shell_snapshot'):cmd+=['--disable',feature]
 cmd+=['-c','web_search="disabled"','-c','project_doc_max_bytes=0','-c','approval_policy="never"','-']
 prompt='Use Intact Simulation to create an editable phone exterior concept, 71.5 mm wide, 147 mm long and 7.8 mm thick. Include a rounded hollow frame, front and rear glass, screen details, three separate rear camera lenses, side buttons, a bottom charging recess and eight 1.2 mm speaker openings. Clearly identify assumptions rather than claiming this is an exact commercial phone or internal assembly. Check the exported frame dimensions and review the front and back before returning STEP and STL links. Then create a separate gyroid sheet lattice in a 20 mm cube with 8 mm cells, dimensionless band 0.4 and 20 samples per cell. Check its exported geometry, show a useful view, and give printable mesh and editable Python links. Use only Intact tools for these models.'
 env={k:v for k,v in os.environ.items() if k not in ('CODEX_THREAD_ID','CODEX_TURN_ID')};env['INTACT_STATE_DIR']=str(ROOT)
 started=time.monotonic()
 with (OUT/'events.jsonl').open('w') as stdout,(OUT/'stderr.log').open('w') as stderr:
  p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,env=env,start_new_session=True,text=True);p.communicate(prompt,timeout=300)
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
 assert all(t in names for t in ('build_model','validate_model','snapshot_model','build_tpms','export_model')),names
 (OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
