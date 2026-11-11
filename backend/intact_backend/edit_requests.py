"""Revision-bound viewer to agent handoff. No browser-supplied Python is executed."""
import base64, binascii, json, re, time, uuid
from copy import deepcopy
from .projects import atomic_json
from .view_settings import ViewSettings

class EditRequests:
    def __init__(self,projects):self.projects=projects
    def path(self,key,request_id):
        self.projects.path(key)
        if not isinstance(request_id,str) or not re.fullmatch('[a-f0-9]{32}',request_id):raise ValueError('Invalid edit request id.')
        return self.projects.models/key/'requests'/(request_id+'.json')
    def resolve(self,key,refs,revision,artifact_id):
        if not isinstance(revision,int) or isinstance(revision,bool) or revision<1:raise ValueError('Geometry revision must be a positive integer.')
        r=self.projects.load(key)
        if revision!=r['spec']['revision'] or artifact_id!=r['spec']['program']['artifact_id']:raise ValueError('Stale geometry selection. Reload the current model and select again.')
        if not isinstance(refs,list) or len(refs)>64 or any(not isinstance(v,str) or len(v)>70 for v in refs):raise ValueError('Choose at most 64 geometry references.')
        topology=json.loads(self.projects.artifact(key,'topology.json').read_text());lookup={}
        for p in r['spec']['parts']:lookup[p['id']]={'ref':p['id'],'kind':'part','part_id':p['id'],'name':p['name'],'measurements':p['measurements']}
        for p in topology['parts']:
            for kind in ('faces','edges','vertices'):
                for f in p[kind]:lookup[f['ref']]=f
        if any(ref not in lookup for ref in refs):raise ValueError('A selected geometry reference does not exist in this CAD artifact.')
        return {'model_id':key,'revision':revision,'artifact_id':artifact_id,'units':'mm','coordinate_system':'cad_z_up','references':[lookup[ref] for ref in dict.fromkeys(refs)]}
    def image(self,item):
        if not isinstance(item,dict) or set(item)-{'name','data_url'}:raise ValueError('Invalid image reference.')
        url=item.get('data_url','');name=item.get('name','reference.png')
        if not isinstance(name,str) or len(name)>150:raise ValueError('Invalid attachment name.')
        if not isinstance(url,str) or len(url)>4*1024*1024:raise ValueError('Each image must be smaller than 3 MB.')
        match=re.fullmatch(r'data:image/(png|jpeg);base64,([A-Za-z0-9+/=]+)',url)
        if not match:raise ValueError('Attach a PNG or JPEG image.')
        try:data=base64.b64decode(match[2],validate=True)
        except binascii.Error as exc:raise ValueError('Invalid image encoding.') from exc
        if len(data)<24 or not (data.startswith(b'\x89PNG\r\n\x1a\n') if match[1]=='png' else data.startswith(b'\xff\xd8\xff')):raise ValueError('Invalid image file.')
        return {'name':name,'data_url':url}
    def create(self,key,data):
        parent_id=data.get('parent_request_id')
        parent=self.read(key,parent_id) if parent_id else None
        if parent and (not parent.get('answer') or parent['status']=='processing'):raise ValueError('Wait for an AI answer before replying.')
        conversation=self.conversation(key,parent) if parent else []
        if len(conversation)>=40:raise ValueError('This conversation is full. Start a new request with your current requirements.')
        intent=data.get('intent',parent.get('intent','edit') if parent else 'edit')
        if intent not in ('edit','question'):raise ValueError('Choose edit or question mode.')
        instructions=data.get('instructions','')
        if not isinstance(instructions,str) or not 1<=len(instructions.strip())<=4000:raise ValueError('Describe the requested edit in 1–4,000 characters.')
        preferences=ViewSettings(annotations=data.get('annotations',[]),measurements=data.get('measurements',[]));drawings=preferences.annotations
        images=data.get('images',[])
        if not isinstance(images,list) or len(images)>4:raise ValueError('Attach up to four reference images.')
        images=[self.image(i) for i in images]
        screenshot=self.image({'name':'annotated-viewport.png','data_url':data['screenshot']}) if data.get('screenshot') else None
        if sum(len(i['data_url']) for i in images)+(len(screenshot['data_url']) if screenshot else 0)>10*1024*1024:raise ValueError('Combined images exceed the 7.5 MB limit.')
        with self.projects.lock(key):
            context=self.resolve(key,data.get('references',[]),data.get('revision'),data.get('artifact_id'))
            if any(m.get('artifact_id')!=context['artifact_id'] for m in preferences.measurements):raise ValueError('A measurement belongs to stale geometry. Select current points before editing.')
            context['measurements']={'provenance':'Viewer annotations in assembled CAD XYZ; verify against native geometry.','items':preferences.measurements}
            parent=self.read(key,parent_id) if parent_id else None
            if parent and not parent['stale']:
                # Replies retain the selected geometry and references from the question.
                if not data.get('references'):context['references']=deepcopy(parent['context']['references'])
                if not images:images=deepcopy(parent.get('images',[]))
                if not screenshot:screenshot=deepcopy(parent.get('screenshot'))
                if not drawings:drawings=deepcopy(parent.get('annotations',[]))
            if sum(len(i['data_url']) for i in images)+(len(screenshot['data_url']) if screenshot else 0)>10*1024*1024:raise ValueError('Combined images exceed the 7.5 MB limit.')
            request_id=data.get('request_id') or uuid.uuid4().hex
            target=self.path(key,request_id)
            if target.exists():raise ValueError('This request ID already exists. Please retry with a new request.')
            request={'request_id':request_id,'parent_request_id':parent_id,'conversation_id':parent.get('conversation_id',parent_id) if parent else request_id,'status':'pending','intent':intent,'created_at':time.time(),'instructions':instructions.strip(),'context':context,'annotations':drawings,'images':images,'screenshot':screenshot,'error':None}
            atomic_json(self.path(key,request['request_id']),request)
        return self.summary(request)
    def summary(self,r):return {'revision':r['context']['revision'],**{k:r.get(k) for k in ('request_id','status','intent','created_at','instructions','error','result_revision','progress','direct_run','answer','geometry_changed','validation','parent_request_id','conversation_id')}}
    def list(self,key):
        self.projects.load(key);items=[]
        for path in (self.projects.models/key/'requests').glob('*.json'):
            r=json.loads(path.read_text());summary=self.summary(r)
            current=self.projects.load(key)
            if r['status'] in ('pending','failed') and (r['context']['revision']!=current['spec']['revision'] or r['context']['artifact_id']!=current['spec']['program']['artifact_id']):summary['status']='stale'
            items.append(summary)
        return sorted(items,key=lambda r:r['created_at'],reverse=True)
    def read(self,key,request_id):
        path=self.path(key,request_id)
        if not path.is_file():raise ValueError('Edit request not found.')
        r=json.loads(path.read_text());current=self.projects.load(key)
        r['current_revision']=current['spec']['revision'];r['stale']=current['spec']['revision']!=r['context']['revision'] or current['spec']['program']['artifact_id']!=r['context']['artifact_id']
        r['conversation']=self.conversation(key,r)
        r['program']=current['spec']['program'] if not r['stale'] else None
        return r
    def conversation(self,key,r):
        messages=[];seen=set()
        while r:
            rid=r['request_id']
            if rid in seen or len(seen)>=20:raise ValueError('Invalid or excessive conversation history.')
            seen.add(rid)
            pair=[{'role':'user','content':r['instructions'],'revision':r['context']['revision']}]
            if r.get('answer'):pair.append({'role':'assistant','content':r['answer']})
            messages=pair+messages
            parent=r.get('parent_request_id')
            r=json.loads(self.path(key,parent).read_text()) if parent else None
        return messages
    def respond(self,key,request_id,message,needs_reply=False):
        if not isinstance(message,str) or not 1<=len(message.strip())<=16000:raise ValueError('Answer must contain 1–16,000 characters.')
        with self.projects.lock(key):
            r=self.read(key,request_id)
            if r.get('direct_run') and r['status']=='processing':raise ValueError('The local AI task owns this request.')
            if r['status'] not in ('pending','succeeded','awaiting_reply','needs_review'):raise ValueError('This request is not available for a response.')
            revision=self.projects.load(key)['spec']['revision']
            if r['intent']=='question' and revision!=r['context']['revision']:raise ValueError('Geometry changed during this question. Start a fresh request.')
            for field in ('conversation','program','current_revision','stale'):r.pop(field,None)
            r.update(answer=message.strip(),status='awaiting_reply' if needs_reply else 'succeeded',result_revision=revision,geometry_changed=revision!=r['context']['revision'])
            atomic_json(self.path(key,request_id),r)
            return self.summary(r)
    def apply(self,key,request_id,source,parameters,cancel_event=None):
        r=self.read(key,request_id)
        if r.get('intent')=='question':raise ValueError('Geometry questions are read-only.')
        if r['stale']:raise ValueError('Stale edit request. Select geometry in the current revision and create a new request.')
        if r['status'] not in ('pending','failed'):raise ValueError('This request is already processing or completed.')
        # Atomically claim the request across concurrent agent connections.
        with self.projects.lock(key):
            fresh=json.loads(self.path(key,request_id).read_text())
            if fresh['status'] not in ('pending','failed'):raise ValueError('This edit request has already been claimed.')
            fresh.update(status='processing',error=None);atomic_json(self.path(key,request_id),fresh)
        try:
            record=self.projects.build(source,parameters,model_id=key,expected_revision=r['context']['revision'],cancel_event=cancel_event)
            fresh.update(status='succeeded',result_revision=record['spec']['revision']);return record
        except BaseException as exc:
            fresh.update(status='failed',error=str(exc)[:2000]);raise
        finally:atomic_json(self.path(key,request_id),fresh)

