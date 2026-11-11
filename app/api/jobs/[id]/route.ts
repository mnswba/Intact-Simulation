import {backendJson} from '@/lib/engineering/backend-proxy';
type Context={params:Promise<{id:string}>};
export async function GET(request:Request,context:Context){const {id}=await context.params;if(!/^[a-f0-9]{32}$/.test(id))return Response.json({error:'Job not found.'},{status:404});return backendJson(request,`/v1/jobs/${id}`);}
export async function DELETE(request:Request,context:Context){const {id}=await context.params;if(!/^[a-f0-9]{32}$/.test(id))return Response.json({error:'Job not found.'},{status:404});return backendJson(request,`/v1/jobs/${id}`,'DELETE');}
