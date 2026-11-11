import {getChatGPTUser} from '@/app/chatgpt-auth';
import {engineeringService} from './service';
export async function authorizedBackend(request:Request,mutation=false){
  if(!await getChatGPTUser())throw new Error('Sign in to use the engineering backend.');
  const origin=request.headers.get('origin');if(mutation&&origin&&origin!==new URL(request.url).origin)throw new Error('Origin is not allowed.');
  const service=engineeringService();if(!service)throw new Error('Connect the Python CAD backend and hosted model account to enable AI generation.');return service;
}
export async function backendJson(request:Request,path:string,method='GET',body?:unknown){
  try{const service=await authorizedBackend(request,method!=='GET');const response=await fetch(service.root+path,{method,headers:service.headers,...(body===undefined?{}:{body:JSON.stringify(body)}),signal:AbortSignal.timeout(12000),redirect:'error'});const data=await response.json() as Record<string,unknown>;return Response.json(data,{status:response.status});}
  catch(e){return Response.json({error:e instanceof Error?e.message:'The engineering service is unreachable.'},{status:503});}
}
