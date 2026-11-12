/** Supported component bridge; annotation mode is deliberately never entered. */
export const hasDirectChat = (host=globalThis.window)=>typeof host?.openai?.sendFollowUpMessage==='function';
export async function dispatchAI(request,{run,host=globalThis.window}){
 if(!hasDirectChat(host)){await run(request);return 'local';}
 const prompt=`Intact viewer request: model_id=${request.model_id}, request_id=${request.request_id}, revision=${request.revision}, intent=${request.intent}.\n${request.instructions}\nFirst read_edit_request for this ID and get_model. Respect selection, source guards and intent; simulation preserves CAD. Execute the request or ask a critical clarification. Finish with respond_to_edit_request so the viewer receives the answer and results.`;
 // A host failure must remain retryable; never start a second task on ambiguous delivery.
 await host.openai.sendFollowUpMessage({prompt,scrollToBottom:true});return 'chatgpt';
}
export async function saveAndDispatchAI(data,{save,...transport}){
 const saved=await save(data);return {request:saved,transport:await dispatchAI(saved,transport)};
}
