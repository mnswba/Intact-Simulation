"""Disposable camera model for browser handoff regression; never edits user models."""
import json,sys
from pathlib import Path
from intact_backend.projects import ProjectService
from intact_backend.viewer_server import viewer_url
from intact_backend.edit_requests import EditRequests
root=Path(sys.argv[1]);s=ProjectService(root)
if len(sys.argv)>2:
 print(json.dumps(EditRequests(s).respond(sys.argv[2],sys.argv[3],'Keep the indicator, or replace it with a camera?',True)))
else:
 r=s.build('import build123d as bd\ndef build(params):\n    return {"camera_glass":bd.Cylinder(2.3,1),"indicator":bd.Pos(10,0,0)*bd.Cylinder(1,1)}',{})
 print(json.dumps({'model_id':r['model_id'],'url':viewer_url(root,r['model_id'])}))
