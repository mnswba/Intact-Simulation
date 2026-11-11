import { validateDesign } from './model.ts';
import type { Design } from './model.ts';
import { defaultStudy } from './analysis.ts';
import type { Study } from './analysis.ts';
export type PartSpec={id:string;name:string;template:Design['kind'];engine:'build123d'|'implicit_mesh';enabled:boolean;material:Design['material'];color:string;params:{length:number;width:number;height:number;holeDiameter:number;finCount:number;wall:number};position:[number,number,number];measurements?:{volume_mm3:number;surface_area_mm2:number;solid_count:number;face_count:number;provenance?:'OpenCASCADE B-rep'|'validated triangle mesh';watertight?:boolean|null;relative_density?:number|null}};
export type DesignSpec={schema_version:1;revision:number;units:'mm';parts:PartSpec[];simulation:{study:Study;approved_fingerprint:string|null};program?:{source:string;parameters:Record<string,number>;artifact_id:string|null;asset_id?:string|null}|null};
export function specFromDesign(d:Design,study:Study={...defaultStudy}):DesignSpec{return {schema_version:1,revision:1,units:'mm',parts:[{id:'main',name:d.name,template:d.kind,engine:'build123d',enabled:true,material:d.material,color:'#6287bc',params:{length:d.length,width:d.width,height:d.height,holeDiameter:d.holeDiameter,finCount:d.finCount,wall:d.wall??3},position:[0,0,0]}],simulation:{study:validateStudy(study),approved_fingerprint:null}};}
export function designFromSpec(spec:DesignSpec,partId?:string):Design{const p=spec.parts.find(p=>p.id===partId)??spec.parts.find(p=>p.enabled)!;return validateDesign({name:p.name,kind:p.template,material:p.material,...p.params,...(p.template==='custom'?{measuredVolume:p.measurements?.volume_mm3}:{})});}
export function replaceDesign(spec:DesignSpec,d:Design,partId?:string):DesignSpec{const checked=validateDesign(d);if(d.kind==='custom')throw new Error('Change the CAD program parameters and rebuild this model.');const part=spec.parts.find(p=>p.id===partId)??spec.parts.find(p=>p.enabled)!;return {...spec,revision:spec.revision+1,parts:spec.parts.map(p=>p.id===part.id?{...p,name:checked.name,template:checked.kind,material:checked.material,params:{length:checked.length,width:checked.width,height:checked.height,holeDiameter:checked.holeDiameter,finCount:checked.finCount,wall:checked.wall??3}}:p),simulation:{...spec.simulation,approved_fingerprint:null}};}
export function replaceStudy(spec:DesignSpec,study:Study):DesignSpec{return {...spec,revision:spec.revision+1,simulation:{study:validateStudy(study),approved_fingerprint:null}};}
export function validateStudy(value:unknown):Study{
  if(!value||typeof value!=='object')throw new Error('A study is required.');const s=value as Study;
  if(s.type!=='mechanical'&&s.type!=='thermal')throw new Error('Unsupported study type.');
  for(const [key,min,max] of [['force',.000001,1e6],['heat',.000001,1e5],['ambient',-100,1000],['convection',.000001,1e5],['nodes',11,101]] as const)if(!Number.isFinite(s[key])||s[key]<min||s[key]>max)throw new Error(`Invalid ${key} setting.`);
  if(!Number.isInteger(s.nodes))throw new Error('Node count must be an integer.');
  return {type:s.type,force:s.force,heat:s.heat,ambient:s.ambient,convection:s.convection,nodes:s.nodes};
}
export function validateSpec(value:unknown):DesignSpec{
  if(!value||typeof value!=='object')throw new Error('A design specification is required.');const s=value as DesignSpec;
  if(s.schema_version!==1||s.units!=='mm'||!Number.isInteger(s.revision)||s.revision<1||!Array.isArray(s.parts)||s.parts.length<1||s.parts.length>128)throw new Error('Unsupported design specification.');
  const ids=new Set<string>();const parts=s.parts.map(p=>{
    if(!p||!/^([a-z][a-z0-9_]{0,47})$/.test(p.id)||ids.has(p.id)||!['build123d','implicit_mesh'].includes(p.engine)||typeof p.enabled!=='boolean'||!/^#[0-9a-fA-F]{6}$/.test(p.color))throw new Error('Invalid part identity or engine.');ids.add(p.id);
    if(p.template==='custom'){const m=p.measurements;if(!m||![m.volume_mm3,m.surface_area_mm2].every(v=>Number.isFinite(v)&&v>0)||![m.solid_count,m.face_count].every(v=>Number.isInteger(v)&&v>0)||m.solid_count>1000||m.face_count>1500000)throw new Error('Generated geometry requires valid kernel measurements.');}
    const d=validateDesign({name:p.name,kind:p.template,material:p.material,...p.params,...(p.template==='custom'?{measuredVolume:p.measurements?.volume_mm3}:{})});
    if(!Array.isArray(p.position)||p.position.length!==3||p.position.some(v=>!Number.isFinite(v)||Math.abs(v)>10000))throw new Error('Invalid part placement.');
    return {...specFromDesign(d).parts[0],id:p.id,engine:p.engine,enabled:p.enabled,color:p.color,...(p.template==='custom'?{measurements:p.measurements}:{}),position:[...p.position] as [number,number,number]};
  });
  if(!parts.some(p=>p.enabled))throw new Error('At least one part must remain enabled.');
  const fingerprint=s.simulation?.approved_fingerprint??null;if(fingerprint!==null&&!/^[a-f0-9]{64}$/.test(fingerprint))throw new Error('Invalid approval fingerprint.');
  let program:DesignSpec['program']=undefined;
  if(s.program){const p=s.program;if(typeof p.source!=='string'||!p.source.trim()||new TextEncoder().encode(p.source).length>120000||!p.parameters||typeof p.parameters!=='object'||Array.isArray(p.parameters)||Object.keys(p.parameters).length>150)throw new Error('Invalid CAD program.');for(const [name,value] of Object.entries(p.parameters))if(!/^[a-z][a-z0-9_]{0,47}$/.test(name)||!Number.isFinite(value)||Math.abs(value)>1e6)throw new Error('Invalid CAD program parameter.');if(p.artifact_id!==null&&!/^[a-f0-9]{64}$/.test(p.artifact_id))throw new Error('Invalid generated model artifact.');if(p.asset_id!=null&&!/^[a-f0-9]{64}$/.test(p.asset_id))throw new Error('Invalid source asset.');program={source:p.source,parameters:{...p.parameters},artifact_id:p.artifact_id,...(p.asset_id?{asset_id:p.asset_id}:{})};}
  if(parts.some(p=>p.template==='custom')&&!program)throw new Error('Generated parts require their CAD program.');
  if(program&&parts.some(p=>p.template!=='custom'))throw new Error('Generated CAD documents must use generated parts.');
  return {schema_version:1,revision:s.revision,units:'mm',parts,simulation:{study:validateStudy(s.simulation?.study),approved_fingerprint:fingerprint},...(program?{program}:{})};
}
export function localSpecKey(spec:DesignSpec){return JSON.stringify({parts:spec.parts,study:spec.simulation.study});}
export type BoundaryRow={face:string;condition:string;value:string;assumption:string};
export function proposedBoundaries(spec:DesignSpec):BoundaryRow[]{const p=spec.parts.find(p=>p.enabled)!;const s=spec.simulation.study;return s.type==='mechanical'?[{face:p.id+'.base',condition:'Fixed support',value:'All beam DOFs',assumption:'Left end clamped'},{face:p.id+'.tip',condition:'Point load',value:`${s.force} N ↓`,assumption:'Downward, at free end'}]:[{face:p.id+'.base',condition:'Heat input',value:`${s.heat} W`,assumption:'Uniform over base'},{face:p.id+'.side_walls',condition:'Convection',value:`${s.convection} W/m²K`,assumption:`Ambient ${s.ambient} °C; fixed h`},{face:p.id+'.tip',condition:'Insulated',value:'0 W',assumption:'No tip heat loss'}];}
