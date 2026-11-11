import type { DesignSpec, PartSpec } from './spec.ts';
import { specFromDesign } from './spec.ts';
import { presets } from './model.ts';
export type SectionAxis='X'|'Y'|'Z';
export const viewerAxisIndex:Record<SectionAxis,number>={X:0,Y:2,Z:1};
export function enclosureAssembly():DesignSpec{
  const base=specFromDesign(presets.box_shell);base.parts[0].name='Enclosure base';base.parts[0].color='#6287bc';
  const lid:PartSpec={...specFromDesign({...presets.beam,name:'Enclosure lid',length:160,width:100,height:3}).parts[0],id:'lid',color:'#9aa7b8',position:[0,0,50]};
  const module:PartSpec={...specFromDesign({...presets.beam,name:'Internal equipment block',length:100,width:60,height:10}).parts[0],id:'module',color:'#63a890',position:[0,0,6]};
  return {...base,parts:[base.parts[0],lid,module]};
}
/** Positions are presentation-only. The source spec is never changed by exploding it. */
export function explodedPositions(parts:PartSpec[],amount:number):Record<string,[number,number,number]>{
  const enabled=parts.filter(p=>p.enabled),factor=Math.max(0,Math.min(3,Number.isFinite(amount)?amount:0));
  const centroid=[0,0,0];for(const p of enabled){centroid[0]+=p.position[0];centroid[1]+=p.position[1];centroid[2]+=p.position[2]+p.params.height/2;}for(let i=0;i<3;i++)centroid[i]/=enabled.length||1;
  return Object.fromEntries(parts.map(p=>{
    const position:[number,number,number]=[p.position[0]+factor*(p.position[0]-centroid[0]),p.position[1]+factor*(p.position[1]-centroid[1]),p.position[2]+factor*(p.position[2]+p.params.height/2-centroid[2])];
    // A concentric internal part stays occluded with a purely vertical offset.
    // Fan it out sideways for inspection; the CAD placement remains untouched.
    const enclosure=enabled.find(q=>q.id!==p.id&&q.template==='box_shell'&&Math.abs(p.position[0]-q.position[0])+p.params.length/2<q.params.length/2&&Math.abs(p.position[1]-q.position[1])+p.params.width/2<q.params.width/2&&p.position[2]>=q.position[2]&&p.position[2]+p.params.height<=q.position[2]+q.params.height);
    if(enclosure)position[0]+=factor*enclosure.params.length*.65;
    return [p.id,position];
  }));
}
/** CAD uses Z up. The Three.js scene uses Y up. */
export function cadToViewer(position:readonly number[]):[number,number,number]{return [position[0],position[2],-position[1]];}
export function sectionCoordinate(min:number,max:number,percent:number){return min+(max-min)*Math.max(0,Math.min(100,percent))/100;}
export function appearanceColor(part:PartSpec,mode:'part'|'material'){
  return mode==='part'?part.color:({aluminum:'#9aa7b8',steel:'#7a8594',copper:'#bb805a'}[part.material]);
}
