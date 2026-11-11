import { materials, validateDesign } from './model.ts';
import type { Design } from './model.ts';
export type Study = { type: 'mechanical' | 'thermal'; force: number; heat: number; ambient: number; convection: number; nodes: number };
export type Point = { x: number; value: number; displacement?: number };
export type Result = { type: Study['type']; comparison?:{quantity:string;unit:string;analytical:number;numerical:number;spread:number;confidence:'Medium'|'Low'}; method: string; points: Point[]; peak: number; tip: number; referenceError: number; balanceError?: number; refinementError?: number; safetyFactor?: number; assumptions: string[]; warnings: string[]; units: string; signature: string };
export const defaultStudy: Study={type:'mechanical',force:25,heat:5,ambient:25,convection:15,nodes:41};
export function signature(d: Design,s:Study){return JSON.stringify([d,s]);}
function solve(matrix: number[][], rhs: number[]) {
  const n=rhs.length, a=matrix.map((r,i)=>[...r,rhs[i]]);
  for(let k=0;k<n;k++){
    let p=k;for(let i=k+1;i<n;i++)if(Math.abs(a[i][k])>Math.abs(a[p][k]))p=i;
    if(Math.abs(a[p][k])<1e-18)throw new Error('The system is singular. Check constraints and dimensions.');
    [a[k],a[p]]=[a[p],a[k]];
    for(let i=k+1;i<n;i++){const f=a[i][k]/a[k][k];for(let j=k;j<=n;j++)a[i][j]-=f*a[k][j];}
  }
  const x=Array(n).fill(0);for(let i=n-1;i>=0;i--){let v=a[i][n];for(let j=i+1;j<n;j++)v-=a[i][j]*x[j];x[i]=v/a[i][i];}return x as number[];
}
function thermal(d:Design,s:Study,n:number){
  const L=d.length/1000,w=d.width/1000,t=d.height/1000,k=materials[d.material].k,A=w*t,P=2*(w+t),dx=L/(n-1),g=k*A/dx;
  const a=Array.from({length:n},()=>Array(n).fill(0)),rhs=Array(n).fill(0);
  for(let i=0;i<n;i++){
    const conv=s.convection*P*dx*(i===0||i===n-1?0.5:1);
    a[i][i]=conv;rhs[i]=conv*s.ambient;
    if(i>0){a[i][i]+=g;a[i][i-1]=-g;}
    if(i<n-1){a[i][i]+=g;a[i][i+1]=-g;}
  }
  rhs[0]+=s.heat;const temp=solve(a,rhs);
  let rejected=0;temp.forEach((T,i)=>{rejected+=s.convection*P*dx*(i===0||i===n-1?0.5:1)*(T-s.ambient);});
  return {temp,rejected};
}
export function runAnalysis(design:Design,s:Study):Result{
  const d=validateDesign(design);
  if(!['mechanical','thermal'].includes(s.type))throw new Error('Unknown analysis type.');
  if(!Number.isInteger(s.nodes)||s.nodes<11||s.nodes>101)throw new Error('Choose 11–101 analysis nodes.');
  if(!Number.isFinite(s.ambient)||s.ambient< -100||s.ambient>1000)throw new Error('Ambient temperature must be between −100 and 1,000 °C.');
  const L=d.length/1000,w=d.width/1000,t=d.height/1000,mat=materials[d.material];
  if(s.type==='mechanical'){
    if(d.kind!=='beam')throw new Error('This study supports a solid rectangular cantilever beam. Select the cantilever template first.');
    if(!Number.isFinite(s.force)||s.force<=0||s.force>1e6)throw new Error('Tip load must be between 0 and 1,000,000 N.');
    const I=w*t**3/12,n=s.nodes,le=L/(n-1),size=2*n;
    const K=Array.from({length:size},()=>Array(size).fill(0)),f=Array(size).fill(0);
    const base=[[12,6*le,-12,6*le],[6*le,4*le**2,-6*le,2*le**2],[-12,-6*le,12,-6*le],[6*le,2*le**2,-6*le,4*le**2]];
    for(let e=0;e<n-1;e++)for(let i=0;i<4;i++)for(let j=0;j<4;j++)K[2*e+i][2*e+j]+=base[i][j]*mat.E*I/le**3;
    f[size-2]=-s.force;
    const u=[0,0,...solve(K.slice(2).map(r=>r.slice(2)),f.slice(2))];
    const exact=s.force*L**3/(3*mat.E*I),tip=Math.abs(u[size-2]),stress=s.force*L*t/(2*I);
    const warnings=[];
    if(L/t<10)warnings.push('Length/thickness is below 10: shear deformation may be significant.');
    if(tip/L>0.05)warnings.push('Deflection exceeds 5% of length. Small-deflection theory may be unsuitable.');
    if(stress>mat.yield)warnings.push('Predicted stress exceeds the representative material yield strength. Linear elasticity is unsuitable beyond yield.');
    return {type:s.type,comparison:{quantity:'Tip displacement',unit:'mm',analytical:exact*1000,numerical:tip*1000,spread:Math.abs(tip-exact)/exact,confidence:warnings.length?'Low':'Medium'},method:'1D Euler–Bernoulli beam finite elements',points:Array.from({length:n},(_,i)=>({x:i/(n-1),value:stress*(1-i/(n-1))/1e6,displacement:u[2*i]*1000})),peak:stress/1e6,tip:tip*1000,referenceError:Math.abs(tip-exact)/exact, safetyFactor:mat.yield/stress,units:'MPa',signature:signature(d,s),warnings,assumptions:['Fixed at x = 0; downward point load at x = L.','Uniform solid rectangular section; linear elastic, small-deflection bending.','Colors show section maximum bending stress along the span, not a 3D stress solution.','Representative room-temperature material properties; no contact, buckling or fatigue.']};
  }
  if(d.kind!=='fin')throw new Error('This study supports a single rectangular cooling fin. Select the cooling-fin template first.');
  if(!Number.isFinite(s.heat)||s.heat<=0||s.heat>1e5||!Number.isFinite(s.convection)||s.convection<=0||s.convection>1e5)throw new Error('Heat input and convection coefficient must be positive and within supported limits.');
  const {temp,rejected}=thermal(d,s,s.nodes),fine=thermal(d,s,2*s.nodes-1),A=w*t,P=2*(w+t),m=Math.sqrt(s.convection*P/(mat.k*A));
  const rise=s.heat/(mat.k*A*m*Math.tanh(m*L));
  const bi=s.convection*(A/P)/mat.k;
  const warnings=[];
  if(bi>0.1)warnings.push('Cross-sectional Biot number exceeds 0.1: the uniform cross-section temperature assumption may be unsuitable.');
  if(temp[0]>150)warnings.push('High temperature: constant room-temperature material properties may be unsuitable.');
  return {type:s.type,comparison:{quantity:'Base temperature',unit:'°C',analytical:s.ambient+rise,numerical:temp[0],spread:Math.abs(temp[0]-s.ambient-rise)/rise,confidence:warnings.length?'Low':'Medium'},method:'1D steady fin · finite-volume conduction',points:temp.map((T,i)=>({x:i/(s.nodes-1),value:T})),peak:temp[0],tip:temp[temp.length-1],referenceError:Math.abs(temp[0]-s.ambient-rise)/rise,refinementError:Math.abs(temp[0]-fine.temp[0])/Math.max(Math.abs(fine.temp[0]-s.ambient),1e-12),balanceError:Math.abs(rejected-s.heat)/s.heat,units:'°C',signature:signature(d,s),warnings,assumptions:['Heat enters at x = 0; tip is insulated.','Uniform convection on four longitudinal sides; constant ambient temperature.','Temperature is uniform across each cross-section; constant thermal conductivity.','No radiation, airflow solution, contact resistance or temperature-dependent properties.']};
}
