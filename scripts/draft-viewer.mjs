// SPDX-License-Identifier: Apache-2.0
import {engineeringPanel} from './viewer/engineering.mjs';
const $=s=>document.querySelector(s);let revision=0,polling=false;
async function request(path,body){const r=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await r.json();if(!r.ok)throw Error(data.error||'Design service unavailable.');return data;}
const error=e=>$('#error').textContent=e.message||String(e),notice=message=>$('#notice').textContent=message;
async function refresh(force=false){const data=await request('engineering.json');if(!data.draft){location.reload();return;}if(!force&&revision===data.revision)return;revision=data.revision;$('#name').textContent=data.name;$('#status').textContent='Draft revision '+revision+' · no solid geometry yet';engineeringPanel($('#engineering'),data,{revision,request,refresh:()=>refresh(true),notice,error});document.body.dataset.ready='true';document.body.dataset.revision=String(revision);}
async function poll(){if(polling)return;polling=true;try{await refresh();}catch(e){error(e);}finally{polling=false;}}
await poll();setInterval(poll,1000);
