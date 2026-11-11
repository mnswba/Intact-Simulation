import * as THREE from 'three';
import type { Design } from './model';
import type { Result } from './analysis';
export function makeGeometry(d: Design): THREE.BufferGeometry {
  if(d.kind==='custom')throw new Error('Generated CAD must use its actual kernel mesh.');
  if(d.kind==='box_shell'){
    const l=d.length/2,w=d.width/2,H=d.height,t=d.wall??3,positions:number[]=[];
    for(const [halfL,halfW,y] of [[l,w,0],[l,w,H],[l-t,w-t,t],[l-t,w-t,H]])for(const [x,z] of [[-halfL,-halfW],[halfL,-halfW],[halfL,halfW],[-halfL,halfW]])positions.push(x,y,z);
    const indices:number[]=[];const quad=(a:number,b:number,c:number,e:number)=>indices.push(a,b,c,a,c,e);
    quad(0,1,2,3);quad(8,11,10,9);
    for(let i=0;i<4;i++){const n=(i+1)%4;quad(i,i+4,n+4,n);quad(i+8,n+8,n+12,i+12);quad(i+4,i+12,n+12,n+4);}
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setIndex(indices);const flat=g.toNonIndexed();g.dispose();flat.computeVertexNormals();return flat;
  }
  if(d.kind==='heatsink'){
    const p=new THREE.Shape(),W=d.width,H=d.height,b=4,f=1.5;
    p.moveTo(-W/2,0);p.lineTo(W/2,0);p.lineTo(W/2,b);
    for(let i=d.finCount-1;i>=0;i--){const left=-W/2+i*(W-f)/(d.finCount-1),right=left+f;p.lineTo(right,b);p.lineTo(right,H);p.lineTo(left,H);p.lineTo(left,b);}
    p.lineTo(-W/2,0);
    const g=new THREE.ExtrudeGeometry(p,{depth:d.length,bevelEnabled:false,steps:1});g.rotateY(Math.PI/2);g.translate(-d.length/2,0,0);return g;
  }
  if(d.kind==='plate'){
    const s=new THREE.Shape(),l=d.length/2,w=d.width/2;
    s.moveTo(-l,-w);s.lineTo(l,-w);s.lineTo(l,w);s.lineTo(-l,w);s.closePath();
    for(const x of [-d.length*.32,d.length*.32])for(const y of [-d.width*.28,d.width*.28]){const h=new THREE.Path();h.absarc(x,y,d.holeDiameter/2,0,2*Math.PI,true);s.holes.push(h);}
    const g=new THREE.ExtrudeGeometry(s,{depth:d.height,bevelEnabled:false,steps:1,curveSegments:48});g.rotateX(-Math.PI/2);return g;
  }
  const g=new THREE.BoxGeometry(d.length,d.height,d.width,60,1,1);g.translate(0,d.height/2,0);return g;
}
export function fieldColor(t:number){const c=new THREE.Color();c.setHSL((1-Math.min(1,Math.max(0,t)))*.66,.78,.53);return c;}
export function colorGeometry(g:THREE.BufferGeometry,d:Design,result:Result,deform:boolean){
  const pos=g.getAttribute('position'),colors=new Float32Array(pos.count*3);
  const values=result.points.map(p=>p.value),lo=result.type==='mechanical'?0:Math.min(...values),hi=Math.max(...values);
  const scale=result.type==='mechanical'&&result.tip>0?Math.min(100,d.length*.1/result.tip):1;
  for(let i=0;i<pos.count;i++){
    const x=Math.max(0,Math.min(1,(pos.getX(i)+d.length/2)/d.length)),p=x*(result.points.length-1),a=Math.floor(p),b=Math.min(a+1,result.points.length-1),t=p-a;
    const value=result.points[a].value*(1-t)+result.points[b].value*t,c=fieldColor((value-lo)/(hi-lo||1));
    colors.set([c.r,c.g,c.b],i*3);
    if(deform&&result.type==='mechanical')pos.setY(i,pos.getY(i)+((result.points[a].displacement??0)*(1-t)+(result.points[b].displacement??0)*t)*scale);
  }
  g.setAttribute('color',new THREE.BufferAttribute(colors,3));g.computeVertexNormals();return scale;
}
export function pythonSource(d:Design){
  if(d.kind==='custom')throw new Error('Export the generated CAD program instead.');
  const header=`# Intact Studio — editable build123d model\n# Dimensions are millimeters. Install build123d to run this script.\nimport build123d as bd\n\nL, W, H = ${d.length}, ${d.width}, ${d.height}\n`;
  if(d.kind==='box_shell')return header+`wall = ${d.wall??3}\nbody = bd.Box(L, W, H, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))\nbody -= bd.Pos(0, 0, wall) * bd.Box(L - 2*wall, W - 2*wall, H - wall + 1, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))\nbd.export_step(body, \"design.step\")\nbd.export_stl(body, \"design.stl\")\n`;
  if(d.kind==='plate')return header+`body = bd.Box(L, W, H)\nfor x in (-L * 0.32, L * 0.32):\n    for y in (-W * 0.28, W * 0.28):\n        body -= bd.Pos(x, y, 0) * bd.Cylinder(${d.holeDiameter/2}, H + 2)\nbd.export_step(body, "design.step")\nbd.export_stl(body, "design.stl")\n`;
  if(d.kind==='heatsink')return header+`base = 4\nfin_thickness = 1.5\ncount = ${d.finCount}\nbody = bd.Pos(0, 0, base / 2) * bd.Box(L, W, base)\nfor i in range(count):\n    y = -W / 2 + fin_thickness / 2 + i * (W - fin_thickness) / (count - 1)\n    body += bd.Pos(0, y, base + (H - base) / 2) * bd.Box(L, fin_thickness, H - base)\nbd.export_step(body, "design.step")\nbd.export_stl(body, "design.stl")\n`;
  return header+`body = bd.Box(L, W, H)\nbd.export_step(body, "design.step")\nbd.export_stl(body, "design.stl")\n`;
}

/** Export the actual assembly positions, independently of presentation tools. */
export function assemblyPythonSource(spec:import('./spec').DesignSpec){
  const lines=['# Intact Studio — editable assembly, millimeters; Z up','import build123d as bd',''];
  const refs:string[]=[];
  for(const [i,p] of spec.parts.filter(p=>p.enabled).entries()){
    const d={name:p.name,kind:p.template,material:p.material,...p.params} as Design;
    const body=pythonSource(d).split('\n').filter(line=>!line.startsWith('#')&&!line.startsWith('import ')&&!line.startsWith('bd.export_'));
    lines.push(`def make_part_${i}():`,...body.filter((line,j)=>line.trim()||j>0).map(line=>'    '+line),'    return body','');
    const correction=['beam','fin','plate'].includes(p.template)?p.params.height/2:0;
    lines.push(`part_${i} = make_part_${i}().moved(bd.Pos(${p.position[0]}, ${p.position[1]}, ${p.position[2]+correction}))`,`part_${i}.label = ${JSON.stringify(p.name)}`,`part_${i}.color = ${JSON.stringify(p.color)}`,'');refs.push(`part_${i}`);
  }
  lines.push(`assembly = bd.Compound(children=[${refs.join(', ')}], label="Intact assembly")`,'bd.export_step(assembly, "assembly.step")','bd.export_stl(assembly, "assembly.stl")','');return lines.join('\n');
}
