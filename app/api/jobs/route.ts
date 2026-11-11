import {validateSpec} from '@/lib/engineering/spec';
import {backendJson} from '@/lib/engineering/backend-proxy';
export async function POST(request:Request){
  try{const raw=await request.text();if(raw.length>180000)return Response.json({error:'Request too large.'},{status:413});const data=JSON.parse(raw);if(typeof data.prompt!=='string'||!data.prompt.trim()||data.prompt.length>4000)throw new Error('Enter a design request of 1–4,000 characters.');return backendJson(request,'/v1/jobs','POST',{prompt:data.prompt,spec:validateSpec(data.spec),contractVersion:3});}
  catch(e){return Response.json({error:e instanceof Error?e.message:'Invalid design request.'},{status:400});}
}
