// SPDX-License-Identifier: Apache-2.0
const cache=new WeakMap();
export async function advancedPanel(container,{request,onResult,readOnly=false}){
 const evidence=await request('engineering-evidence.json'),queue=await request('engineering-jobs.json');const signature=JSON.stringify([readOnly,evidence.reports.map(r=>[r.report_id,r.stale]),queue.jobs.map(j=>[j.job_id,j.status,j.progress])]);if(cache.get(container)===signature)return;cache.set(container,signature);container.replaceChildren();
 const p=document.createElement('p');p.className='muted';p.textContent='Ask AI or ChatGPT to run an engineering study, review or background job. Results are tied to the saved geometry. Scalar overlays show the assembled surface; use Show CAD for cuts/explosion, or VTU for volume postprocessing.';container.append(p);
 const clear=document.createElement('button');clear.textContent='Show CAD';clear.onclick=()=>onResult(null);container.append(clear);
 for(const r of evidence.reports){
  const box=document.createElement('details');const summary=document.createElement('summary');summary.textContent=(r.kind||r.process||r.representation||'Engineering report')+(r.stale?' · stale':'')+(r.verified===false?' · convergence unverified':'');box.append(summary);
  const scope=document.createElement('p');scope.className='muted';scope.textContent=r.scope||'';box.append(scope);
  if(r.study_definition){const s=r.study_definition,p=document.createElement('p');p.textContent=r.kind==='thermal'?`k = ${s.conductivity_w_mk} W/(m K) · ends ${s.low_value} / ${s.high_value} K · source ${s.heat_source_w_m3} W/m³`:r.kind==='structural'?`E = ${s.young_modulus_pa} Pa · ν = ${s.poisson_ratio} · force ${s.force_n.join(', ')} N`:`μ = ${s.viscosity_pa_s} Pa s · Δp = ${s.pressure_drop_pa} Pa · ρ = ${s.density_kg_m3} kg/m³`;box.append(p);}
  if(r.relative_residual!==undefined){const text=document.createElement('p');text.textContent=`Residual ${r.relative_residual.toExponential(2)} · balance ${r.relative_balance_error.toExponential(2)} · ${r.tetrahedra} tetrahedra`;box.append(text);}
  if(r.field_name){const b=document.createElement('button');b.textContent='Show '+r.field_name.replaceAll('_',' ');b.disabled=r.stale;b.onclick=async()=>onResult(await request('engineering-file?report_id='+r.report_id+'&file=report.json'));box.append(b);const legend=document.createElement('p');legend.textContent=`${r.minimum.toPrecision(5)} → ${r.maximum.toPrecision(5)} · ${r.field_name}`;box.append(legend);const v=document.createElement('a');v.textContent='Download VTU';v.href='engineering-file?report_id='+r.report_id+'&file=results.vtu';v.download='results.vtu';box.append(v);}
  const pdf=document.createElement('a');if(r.views){pdf.textContent='Download reference PDF';pdf.href='engineering-file?report_id='+r.report_id+'&file=drawing.pdf';box.append(pdf);}
  if(r.findings)for(const f of r.findings){const item=document.createElement('p');item.textContent=f.check+': '+f.status;box.append(item);}
  container.append(box);
 }
 for(const job of queue.jobs.slice(-12).reverse()){
  const item=document.createElement('p');item.textContent=`${job.operation}: ${job.status} · ${job.progress||''}${job.error?' · '+job.error:''}`;
  if(['queued','running'].includes(job.status)){const b=document.createElement('button');b.textContent='Cancel job';b.disabled=readOnly;b.onclick=async()=>{await request('engineering-job',{action:'cancel',job_id:job.job_id});b.disabled=true;};item.append(b);}container.append(item);
 }
}
