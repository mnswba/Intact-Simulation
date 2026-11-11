/** Current model first, followed by four most recently saved other models. */
export function recentModels(models,current){
 const unique=new Map();
 for(const model of models)if(model?.model_id&&!unique.has(model.model_id))unique.set(model.model_id,model);
 const active={...(unique.get(current.model_id)||{}),model_id:current.model_id,name:current.name};
 unique.delete(current.model_id);
 const recent=[...unique.values()].sort((a,b)=>(Number(b.updated_at)||0)-(Number(a.updated_at)||0)||a.model_id.localeCompare(b.model_id));
 return [active,...recent.slice(0,4)];
}
export function renderModelLibrary(container,current,models,pathname){
 const items=recentModels(models,current),signature=JSON.stringify([pathname,items]);
 if(container.dataset.signature===signature)return;
 container.dataset.signature=signature;
 const links=items.map(model=>{const a=document.createElement('a');a.textContent=model.name+(model.model_id===current.model_id?' · current':'');a.href=pathname.replace(current.model_id,model.model_id);a.dataset.modelId=model.model_id;if(model.model_id===current.model_id)a.setAttribute('aria-current','page');return a;});
 container.replaceChildren(...links);
}
