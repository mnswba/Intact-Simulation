"""Sandboxed PyBullet rigid-body dynamics or explicitly prescribed kinematics."""
import csv,json,math,resource,sys,traceback,zipfile
from pathlib import Path
from xml.etree.ElementTree import Element,SubElement,ElementTree
resource.setrlimit(resource.RLIMIT_CPU,(160,160));resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
import numpy as np
import pybullet as p

def main():
 s=json.loads(Path('/input/request.json').read_text());model=json.loads(Path('/input/model.json').read_text());mesh=json.loads(Path('/input/mesh.json').read_text());parts={part['id']:part for part in model['spec']['parts']};bodies={b['part_id']:b for b in s['bodies']};joints={j['child']:j for j in s['joints']};by_id={j['id']:j for j in s['joints']};roots=[key for key in bodies if key not in joints];frame_origins={key:np.array(joints[key]['origin_mm'] if key in joints else parts[key]['position'],dtype=float) for key in bodies};local_com={};inertias={}
 work=Path('/work');meshes=work/'meshes';meshes.mkdir()
 for item in mesh['parts']:
  key=item['id'];part=parts[key];body=bodies[key];points=np.asarray(item['positions']).reshape(-1,3);world=np.column_stack((points[:,0],-points[:,2],points[:,1]))+np.array(part['position']);lo=world.min(0);hi=world.max(0);size=(hi-lo)*.001;com=np.array(body['center_of_mass_mm'] if body.get('center_of_mass_mm') is not None else (lo+hi)/2);local_com[key]=(com-frame_origins[key])*.001
  if body.get('inertia_kg_m2') is not None:
   xx,yy,zz,xy,xz,yz=body['inertia_kg_m2'];tensor=np.array([[xx,xy,xz],[xy,yy,yz],[xz,yz,zz]]);eig=np.linalg.eigvalsh(tensor)
   if eig.min()<=0 or eig.max()>eig.sum()/2+1e-12:raise ValueError('Body inertia must be positive definite with physical principal moments: '+key)
  else:
   xx,yy,zz=np.maximum(body['mass_kg']/12*np.array([size[1]**2+size[2]**2,size[0]**2+size[2]**2,size[0]**2+size[1]**2]),1e-14);xy=xz=yz=0
  inertias[key]=[float(v) for v in (xx,yy,zz,xy,xz,yz)]
  vertices=(world-frame_origins[key])*.001
  with (meshes/(key+'.obj')).open('w') as stream:
   if s['collision_model']=='box':
    center=(lo+hi)/2;corners=np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])]);vertices=(corners-frame_origins[key])*.001
    from scipy.spatial import ConvexHull
    faces=ConvexHull(vertices).simplices
   else:faces=np.asarray(item['indices']).reshape(-1,3)
   for point in vertices:stream.write('v '+' '.join(format(float(v),'.12g') for v in point)+'\n')
   for tri in faces:stream.write('f '+' '.join(str(int(v)+1) for v in tri)+'\n')
 def fmt(values):return ' '.join(format(float(v),'.12g') for v in values)
 connected={}
 for root in roots:
  members=[]
  for key in bodies:
   cursor=key
   while cursor in joints:cursor=joints[cursor]['parent']
   if cursor==root:members.append(key)
  connected[root]=members;robot=Element('robot',name='intact_'+root)
  for key in members:
   link=SubElement(robot,'link',name=key);inertial=SubElement(link,'inertial');SubElement(inertial,'origin',xyz=fmt(local_com[key]),rpy='0 0 0');SubElement(inertial,'mass',value=str(bodies[key]['mass_kg']));xx,yy,zz,xy,xz,yz=inertias[key];SubElement(inertial,'inertia',ixx=str(xx),iyy=str(yy),izz=str(zz),ixy=str(xy),ixz=str(xz),iyz=str(yz))
   collision=SubElement(link,'collision');geometry=SubElement(collision,'geometry');SubElement(geometry,'mesh',filename='meshes/'+key+'.obj',scale='1 1 1')
   if key in joints:
    j=joints[key];joint=SubElement(robot,'joint',name=j['id'],type={'slider':'prismatic'}.get(j['kind'],j['kind']));SubElement(joint,'parent',link=j['parent']);SubElement(joint,'child',link=key);SubElement(joint,'origin',xyz=fmt((frame_origins[key]-frame_origins[j['parent']])*.001),rpy='0 0 0');axis=np.array(j['axis'],dtype=float);axis/=np.linalg.norm(axis);SubElement(joint,'axis',xyz=fmt(axis));scale=.001 if j['kind']=='slider' else math.pi/180
    if j['kind']!='fixed':SubElement(joint,'limit',lower=str(j['minimum']*scale),upper=str(j['maximum']*scale),effort=str(j['maximum_effort']),velocity='1000');SubElement(joint,'dynamics',damping='0.0001',friction='0')
  ElementTree(robot).write(work/(root+'.urdf'),encoding='utf-8',xml_declaration=True)
 client=p.connect(p.DIRECT)
 try:
  p.setTimeStep(1/240);p.setPhysicsEngineParameter(numSolverIterations=100,deterministicOverlappingPairs=1);p.setGravity(*s['gravity_m_s2'])
  if s['ground']:
   plane=p.createCollisionShape(p.GEOM_PLANE,planeNormal=[0,0,1]);floor=p.createMultiBody(baseMass=0,baseCollisionShapeIndex=plane,basePosition=[0,0,s['ground_z_mm']*.001]);p.changeDynamics(floor,-1,lateralFriction=1)
  mapping={};motors={};root_ids={}
  for root,members in connected.items():
   flags=p.URDF_USE_INERTIA_FROM_FILE
   if s['self_collision']:flags|=p.URDF_USE_SELF_COLLISION|p.URDF_USE_SELF_COLLISION_EXCLUDE_PARENT
   uid=p.loadURDF(str(work/(root+'.urdf')),basePosition=(frame_origins[root]*.001).tolist(),useFixedBase=bodies[root]['fixed'] or s['mode']=='kinematic',flags=flags);root_ids[root]=uid;mapping[root]=(uid,-1)
   if s['mode']=='dynamics':p.resetBaseVelocity(uid,linearVelocity=(np.array(bodies[root]['linear_velocity_mm_s'])*.001).tolist(),angularVelocity=np.radians(bodies[root]['angular_velocity_deg_s']).tolist())
   for index in range(p.getNumJoints(uid)):
    info=p.getJointInfo(uid,index);key=info[12].decode();name=info[1].decode();mapping[key]=(uid,index);j=by_id[name];scale=.001 if j['kind']=='slider' else math.pi/180
    if j['kind']!='fixed':p.resetJointState(uid,index,j['initial']*scale);p.setJointMotorControl2(uid,index,p.VELOCITY_CONTROL,force=0);p.enableJointForceTorqueSensor(uid,index,True);motors[name]=(uid,index,j,scale)
   for key in members:
    body=bodies[key];p.changeDynamics(uid,mapping[key][1],lateralFriction=body['friction'],restitution=body['restitution'],collisionMargin=s['collision_margin_mm']*.001)
  def target(j,t):return j['target']+j['amplitude']*math.sin(2*math.pi*j['frequency_hz']*t+math.radians(j['phase_deg'])) if j['mode']=='sine' else j['initial']+j['target']*t if j['mode']=='velocity' else j['initial']+(j['target']-j['initial'])*min(t/s['duration_s'],1) if j['mode']=='position' and s['mode']=='kinematic' else j['target'] if j['mode']=='position' else j['initial']
  def drive(t):
   if s['mode']=='kinematic':
    for root,uid in root_ids.items():
     elapsed=0 if bodies[root]['fixed'] else t;q=p.getQuaternionFromEuler(np.radians(bodies[root]['angular_velocity_deg_s'])*elapsed);origin=frame_origins[root]*.001+np.array(bodies[root]['linear_velocity_mm_s'])*.001*elapsed;dyn=p.getDynamicsInfo(uid,-1);com,orientation=p.multiplyTransforms(origin.tolist(),q,dyn[3],dyn[4]);p.resetBasePositionAndOrientation(uid,com,orientation)
   for name,(uid,index,j,scale) in motors.items():
    value=target(j,t)
    if j['kind']!='continuous':value=float(np.clip(value,j['minimum'],j['maximum']))
    if s['mode']=='kinematic':
     velocity=j['amplitude']*2*math.pi*j['frequency_hz']*math.cos(2*math.pi*j['frequency_hz']*t+math.radians(j['phase_deg'])) if j['mode']=='sine' else j['target'] if j['mode']=='velocity' else (j['target']-j['initial'])/s['duration_s'] if j['mode']=='position' and t<s['duration_s'] else 0
     if j['kind']!='continuous' and (value<=j['minimum'] and velocity<0 or value>=j['maximum'] and velocity>0):velocity=0
     p.resetJointState(uid,index,value*scale,targetVelocity=velocity*scale);continue
    if j['mode'] in ('position','sine'):p.setJointMotorControl2(uid,index,p.POSITION_CONTROL,targetPosition=value*scale,force=j['maximum_effort'])
    elif j['mode']=='velocity':p.setJointMotorControl2(uid,index,p.VELOCITY_CONTROL,targetVelocity=j['target']*scale,force=j['maximum_effort'])
    elif j['mode']=='torque':p.setJointMotorControl2(uid,index,p.TORQUE_CONTROL,force=float(np.clip(j['target'],-j['maximum_effort'],j['maximum_effort'])))
  def record(t):
   poses={};states={}
   for key,(uid,index) in mapping.items():
    if index<0:
     com,orientation=p.getBasePositionAndOrientation(uid);dyn=p.getDynamicsInfo(uid,-1);inv_pos,inv_q=p.invertTransform(dyn[3],dyn[4]);link_origin,q=p.multiplyTransforms(com,orientation,inv_pos,inv_q);origin=np.array(link_origin);rotation=np.array(p.getMatrixFromQuaternion(q)).reshape(3,3)
    else:
     state=p.getLinkState(uid,index,computeForwardKinematics=True);origin=np.array(state[4]);q=state[5];rotation=np.array(p.getMatrixFromQuaternion(q)).reshape(3,3)
    part_origin=(origin+rotation@((np.array(parts[key]['position'])-frame_origins[key])*.001))*1000
    if not np.isfinite(part_origin).all() or np.max(np.abs(part_origin))>1e8:raise ValueError('Rigid-body simulation diverged; review masses, inertias and contacts.')
    poses[key]={'position_mm':part_origin.tolist(),'quaternion_xyzw':list(q)}
   for name,(uid,index,j,scale) in motors.items():
    state=p.getJointState(uid,index);states[name]={'position':state[0]/scale,'velocity':state[1]/scale,'effort':state[3] if s['mode']=='dynamics' else None,'units':'mm, mm/s, N' if j['kind']=='slider' else 'deg, deg/s, N m'}
   contacts=p.getContactPoints();return {'time_s':t,'poses':poses,'joints':states,'contacts':len(contacts),'total_normal_force_n':sum(c[9] for c in contacts) if s['mode']=='dynamics' else None}
  if s['mode']=='kinematic':drive(0);p.performCollisionDetection()
  frames=[record(0)];steps=round(s['duration_s']*240);next_sample=1/s['sample_hz']
  for step in range(1,steps+1):
   t=step/240;drive(t)
   if s['mode']=='dynamics':p.stepSimulation()
   else:p.performCollisionDetection()
   if t+1e-10>=next_sample or step==steps:frames.append(record(t));next_sample+=1/s['sample_hz']
  with (work/'trajectory.csv').open('w',newline='') as stream:
   writer=csv.writer(stream);writer.writerow(['time_s','part_id','x_mm','y_mm','z_mm','qx','qy','qz','qw'])
   for frame in frames:
    for key,pose in frame['poses'].items():writer.writerow([frame['time_s'],key,*pose['position_mm'],*pose['quaternion_xyzw']])
  with (work/'joints.csv').open('w',newline='') as stream:
   writer=csv.writer(stream);writer.writerow(['time_s','joint_id','position','velocity','effort','units'])
   for frame in frames:
    for key,state in frame['joints'].items():writer.writerow([frame['time_s'],key,state['position'],state['velocity'],state['effort'],state['units']])
  (work/'motion-settings.json').write_text(json.dumps(s))
  with zipfile.ZipFile(work/'rig.zip','w',zipfile.ZIP_DEFLATED) as archive:
   for file in [*work.glob('*.urdf'),*meshes.glob('*.obj'),work/'motion-settings.json']:archive.write(file,file.relative_to(work))
  initial=frames[0]['poses'];last=frames[-1]['poses'];displacements={key:(np.array(last[key]['position_mm'])-initial[key]['position_mm']).tolist() for key in roots}
  report={'kind':'motion','name':s['name'],'mode':s['mode'],'frames':frames,'duration_s':s['duration_s'],'sample_hz':s['sample_hz'],'frame_count':len(frames),'root_displacement_mm':displacements,'maximum_contact_count':max(f['contacts'] for f in frames),'joint_count':len(motors),'solver':'PyBullet DIRECT','verified':False,'study_definition':s,'scope':'Rigid-body motors, gravity and contact; convex-hull/box colliders and bounding-box inertia unless overridden. No flexible-body stress or autonomous balance controller.' if s['mode']=='dynamics' else 'Prescribed root/joint trajectories; geometric contact queries only. No dynamic force or walking-stability prediction.','inertia_source':'User-provided inertia or box approximation about supplied/box-center COM','collision_model':s['collision_model'],'files':['trajectory.csv','joints.csv','rig.zip']}
  (work/'report.json').write_text(json.dumps(report,allow_nan=False))
 finally:p.disconnect(client)
try:main()
except BaseException as exc:Path('/work/error.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()[-3000:]}));sys.exit(1)
