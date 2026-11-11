const NS='http://www.w3.org/2000/svg';
export function drawing(svg,view,onChange,onActivity){
 let tool='select',color='#ff7b54',width=3,active=null,start=null,undo=[],redo=[];
 const node=(tag,attrs)=>{const n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);return n;};
 function element(item,w,h){const pts=item.points.map(([x,y])=>[x*w,y*h]),[a,b=a]=pts;let e;const common={stroke:item.color,'stroke-width':item.width,fill:'none','stroke-linecap':'round','stroke-linejoin':'round'};
  if(item.tool==='pen')e=node('polyline',{...common,points:pts.map(p=>p.join(',')).join(' ')});
  if(item.tool==='line'||item.tool==='arrow'){e=node('g',{});e.append(node('line',{...common,x1:a[0],y1:a[1],x2:b[0],y2:b[1]}));if(item.tool==='arrow'){const angle=Math.atan2(b[1]-a[1],b[0]-a[0]),s=12+item.width;e.append(node('polyline',{...common,points:[[b[0]-s*Math.cos(angle-.5),b[1]-s*Math.sin(angle-.5)],b,[b[0]-s*Math.cos(angle+.5),b[1]-s*Math.sin(angle+.5)]].map(p=>p.join(',')).join(' ')}));}}
  if(item.tool==='rectangle'||item.tool==='fill')e=node('rect',{...common,x:Math.min(a[0],b[0]),y:Math.min(a[1],b[1]),width:Math.abs(a[0]-b[0]),height:Math.abs(a[1]-b[1]),...(item.tool==='fill'?{fill:item.color,'fill-opacity':.2}:{})});
  if(item.tool==='ellipse')e=node('ellipse',{...common,cx:(a[0]+b[0])/2,cy:(a[1]+b[1])/2,rx:Math.abs(a[0]-b[0])/2,ry:Math.abs(a[1]-b[1])/2});
  if(item.tool==='text'){e=node('text',{x:a[0],y:a[1],fill:item.color,'font-size':Math.max(14,item.width*5),'font-family':'system-ui'});e.textContent=item.text;}
  e.dataset.id=item.id;return e;
 }
 function render(){svg.replaceChildren();const {width:w,height:h}=svg.getBoundingClientRect();view.annotations.forEach(item=>svg.append(element(item,w,h)));}
 function checkpoint(){undo.push(structuredClone(view.annotations));if(undo.length>40)undo.shift();redo=[];}
 function point(e){const r=svg.getBoundingClientRect();return [Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))];}
 svg.addEventListener('pointerdown',e=>{if(['select','pan'].includes(tool))return;e.preventDefault();svg.setPointerCapture(e.pointerId);checkpoint();start=point(e);
  if(tool==='eraser'){const target=e.target.closest('[data-id]');view.annotations=view.annotations.filter(i=>i.id!==target?.dataset.id);render();onChange();return;}
  if(tool==='move'){const target=e.target.closest('[data-id]');active=view.annotations.find(i=>i.id===target?.dataset.id);if(active)active._original=structuredClone(active.points);return;}
  if(view.annotations.length>=300)return;
  active={id:crypto.randomUUID(),tool,color,width,points:[start,start]};if(tool==='text'){active.text=document.querySelector('#drawing-text').value||'Note';active.points=[start];}view.annotations.push(active);render();
 });
 svg.addEventListener('pointermove',e=>{if(!active)return;const p=point(e);if(tool==='move'){active.points=active._original.map(([x,y])=>[Math.max(0,Math.min(1,x+p[0]-start[0])),Math.max(0,Math.min(1,y+p[1]-start[1]))]);}else if(tool==='pen'){if(active.points.length<2000)active.points.push(p);}else if(tool!=='text')active.points[1]=p;render();});
 const end=()=>{if(active){delete active._original;active=null;onChange();}};svg.addEventListener('pointerup',end);svg.addEventListener('pointercancel',end);
 new ResizeObserver(render).observe(svg);
 return {render,reset(){undo=[];redo=[];active=null;},setTool(value){end();tool=value;svg.style.pointerEvents=['select','pan'].includes(tool)?'none':'auto';svg.style.cursor=tool==='move'?'move':tool==='eraser'?'cell':'crosshair';onActivity(!['select','pan'].includes(tool));},setColor(v){color=v;},setWidth(v){width=Number(v);},undo(){if(undo.length){redo.push(structuredClone(view.annotations));view.annotations=undo.pop();render();onChange();}},redo(){if(redo.length){undo.push(structuredClone(view.annotations));view.annotations=redo.pop();render();onChange();}},clear(){checkpoint();view.annotations=[];render();onChange();},async composite(canvas,overlay){
  const result=document.createElement('canvas');result.width=canvas.width;result.height=canvas.height;const ctx=result.getContext('2d');ctx.drawImage(canvas,0,0);if(overlay)overlay(ctx,result.width,result.height);const clone=svg.cloneNode(true);clone.setAttribute('xmlns',NS);clone.setAttribute('width',result.width);clone.setAttribute('height',result.height);const r=svg.getBoundingClientRect();clone.setAttribute('viewBox',`0 0 ${r.width} ${r.height}`);const blob=new Blob([new XMLSerializer().serializeToString(clone)],{type:'image/svg+xml'}),url=URL.createObjectURL(blob);try{const image=new Image();image.src=url;await image.decode();ctx.drawImage(image,0,0,result.width,result.height);}finally{URL.revokeObjectURL(url);}return result;
 }};
}
