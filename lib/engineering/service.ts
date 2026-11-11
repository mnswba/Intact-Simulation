/** Server-only service configuration. Credentials never enter client responses. */
export function engineeringService(){
  const base=process.env.INTACT_BACKEND_URL?.replace(/\/$/,'');
  const endpoint=base?`${base}/v1/design`:process.env.DESIGN_SERVICE_URL;
  if(!endpoint)return null;
  const design=new URL(endpoint);if(design.protocol!=='https:'&&!(process.env.NODE_ENV!=='production'&&['localhost','127.0.0.1'].includes(design.hostname)))throw new Error('The engineering service requires HTTPS.');
  const health=base?`${base}/health`:new URL('/health',design).toString();
  const token=process.env.INTACT_BACKEND_TOKEN||process.env.DESIGN_SERVICE_TOKEN;
  const root=base||design.toString().replace(/\/v1\/design\/?$/,'').replace(/\/$/,'');
  return {root,design:design.toString(),health,headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`}:{})}};
}
