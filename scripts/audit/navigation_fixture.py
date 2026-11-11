"""Disposable sidebar models; never writes to the user's installed project store."""
import json,os,sys
from pathlib import Path
from intact_backend.projects import ProjectService
from intact_backend.viewer_server import viewer_url
root=Path(sys.argv[1]);s=ProjectService(root)
source='import build123d as bd\ndef build(params):\n    return {"camera_glass":bd.Cylinder(2.3,1),"indicator":bd.Pos(10,0,0)*bd.Cylinder(1,1)}'
if sys.argv[2]=='new':
 r=s.build(source,{},name='Newest live model');print(json.dumps({'model_id':r['model_id']}))
else:
 current=s.build(source,{},name='Current older model');os.utime(s.path(current['model_id']),(500,500));others=[]
 for index in range(6):
  r=s.build(source,{},name='Recent '+str(index));os.utime(s.path(r['model_id']),(1000+index,1000+index));others.append(r['model_id'])
 print(json.dumps({'model_id':current['model_id'],'others':others,'url':viewer_url(root,current['model_id'])}))
