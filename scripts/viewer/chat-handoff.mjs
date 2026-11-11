/** ChatGPT browser annotation API: invoke synchronously from the user's click. */
export function hasChatHandoff(doc=document){return typeof doc.oai?.annotation?.request==='function';}
export function chatHandoff(target,{instructions,model_id,request_id,revision,intent},doc=document){
 if(!hasChatHandoff(doc))return {available:false,accepted:false};
 // The full description remains in the visible target and persisted request.
 const initialComment=instructions.length<=240?instructions:'Please handle the attached Intact CAD request and its full description.';
 const metadata={model_id,request_id,revision,intent,workflow:'Intact Ask AI: read_edit_request, edit or clarify, respond_to_edit_request'};
 const result=doc.oai.annotation.request(target,{initialComment,metadata,mode:'advanced',enterAnnotationMode:true,omitScreenshot:false});
 return {available:true,accepted:result?.accepted===true};
}
