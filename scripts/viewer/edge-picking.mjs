/** Pixel-space native edge picking, independent of zoom and camera projection. */
export function closestEdgeCandidates(segments,x,y,radius=16,limit=32){
 const nearest=new Map();
 for(const segment of segments){const {a,b}=segment;if(!a||!b||[...a,...b].some(n=>!Number.isFinite(n))||a[2]<-1||a[2]>1||b[2]<-1||b[2]>1||a[3]<=0||b[3]<=0)continue;
  if(x<Math.min(a[0],b[0])-radius||x>Math.max(a[0],b[0])+radius||y<Math.min(a[1],b[1])-radius||y>Math.max(a[1],b[1])+radius)continue;
  const dx=b[0]-a[0],dy=b[1]-a[1],u=Math.max(0,Math.min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy||1))),distance=Math.hypot(a[0]+u*dx-x,a[1]+u*dy-y);
  if(distance>radius||nearest.has(segment.ref)&&nearest.get(segment.ref).distance<=distance)continue;
  // Correct interpolation after perspective division, rather than treating
  // screen-space u as the original 3D segment parameter.
  const t=(u/b[3])/((1-u)/a[3]+u/b[3]);
  nearest.set(segment.ref,{ref:segment.ref,partId:segment.partId,distance,screen:[a[0]+u*dx,a[1]+u*dy],world:segment.worldA.map((n,i)=>n+(segment.worldB[i]-n)*t)});
 }
 return [...nearest.values()].sort((a,b)=>a.distance-b.distance||a.ref.localeCompare(b.ref)).slice(0,limit);
}
