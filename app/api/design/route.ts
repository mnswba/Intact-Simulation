import { getChatGPTUser } from '@/app/chatgpt-auth';
export async function GET(){return Response.json({available:false,backend_ready:false,agent:'chatgpt',mode:'chatgpt',external_model_service:false,reason:'Use Intact Simulation in your ChatGPT conversation. No separate model provider is required.'});}
export async function POST(request:Request){
  const user=await getChatGPTUser();if(!user)return Response.json({error:'Sign in to use the workspace.'},{status:401});
  const origin=request.headers.get('origin');if(origin&&origin!==new URL(request.url).origin)return Response.json({error:'Origin is not allowed.'},{status:403});
  return Response.json({error:'Describe your design in ChatGPT with the Intact Simulation plugin enabled. The standalone website does not invoke an AI model.',plugin:'intact-simulation',external_model_service:false},{status:409});
}
