import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {STLExporter} from 'three/addons/exporters/STLExporter.js';
import {EXAMPLES, CHATGPT_PROMPT, parseRecipe} from './core.mjs';

const $ = id => document.getElementById(id);
const status = (message, error = false) => { $('status').textContent = message; $('status').classList.toggle('error', error); };
const recipeText = recipe => JSON.stringify(recipe, null, 2);
let worker, timeout, sequence = 0, built = null, draft = structuredClone(EXAMPLES.flange), mesh, busy = false;
const history = [];
let scene, camera, renderer, controls, grid;
function initViewer() {
  const host = $('viewport');
  renderer = new THREE.WebGLRenderer({antialias:true, alpha:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setClearColor(0x000000, 0);
  host.append(renderer.domElement); scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xffffff,0x536773,2.5));
  const light = new THREE.DirectionalLight(0xffffff, 3); light.position.set(50,-60,100); scene.add(light);
  camera = new THREE.PerspectiveCamera(38,1,.01,100000); camera.up.set(0,0,1);
  controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true;
  grid = new THREE.GridHelper(200,20,0x93aab5,0xb6c8d0); grid.rotation.x = Math.PI/2;
  grid.material.transparent = true; grid.material.opacity = .45; grid.material.depthWrite = false; scene.add(grid);
  new ResizeObserver(() => { const {width,height} = host.getBoundingClientRect(); renderer.setSize(width,height); camera.aspect=width/height; camera.updateProjectionMatrix(); }).observe(host);
  renderer.setAnimationLoop(() => {controls.update(); renderer.render(scene,camera);});
  $('loading').remove();
}
function fit(reset = false, bottom = false) {
  if (!mesh) return;
  const box = new THREE.Box3().setFromObject(mesh), center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3()), radius = Math.max(size.length()/2, .1);
  const angle = Math.atan(Math.tan(THREE.MathUtils.degToRad(camera.fov/2))*Math.min(camera.aspect,1));
  const distance = radius / Math.sin(angle) * 1.12;
  let direction = camera.position.clone().sub(controls.target).normalize();
  if (reset) direction = new THREE.Vector3(1,-1,.85).normalize();
  if (bottom) direction = new THREE.Vector3(0,-.001,-1).normalize();
  controls.target.copy(center); camera.position.copy(center).addScaledVector(direction,distance);
  camera.near=Math.max(.01,distance-radius*2); camera.far=distance+radius*20;
  camera.updateProjectionMatrix(); controls.update();
}
const workerURL = typeof INTACT_WORKER_SOURCE === 'undefined' ? new URL('./worker.js',import.meta.url) : URL.createObjectURL(new Blob([INTACT_WORKER_SOURCE],{type:'text/javascript'}));
function restartWorker() { worker?.terminate(); worker = new Worker(workerURL,{type:typeof INTACT_WORKER_SOURCE==='undefined'?'module':'classic'}); return worker; }
function setBusy(value) { busy=value; $('cancel').disabled=!value; for(const id of ['build','apply','flange','bracket','box']) $(id).disabled=value; $('undo').disabled=value||!history.length; }
function stop(message) { clearTimeout(timeout); worker?.terminate(); sequence++; setBusy(false); status(message,true); }
function showParameters(recipe) {
  const host = $('parameters'); host.replaceChildren();
  const primitives = recipe.nodes.filter(n=>['box','sphere','cylinder'].includes(n.type));
  for (const node of primitives) {
    const section = document.createElement('div'); section.className='param-node';
    const title = document.createElement('h3'); title.textContent=`${node.id} · ${node.type}`; section.append(title);
    const fields = document.createElement('div'); fields.className='param-fields';
    const keys = node.type==='box' ? ['size.0','size.1','size.2'] : node.type==='cylinder' ? ['radius','height',...(node.radiusTop!==undefined?['radiusTop']:[])] : ['radius'];
    const labels = {'size.0':'X · mm','size.1':'Y · mm','size.2':'Z · mm',radius:'Radius · mm',height:'Height · mm',radiusTop:'Top R · mm'};
    for (const key of keys) {
      const label=document.createElement('label');label.textContent=labels[key];
      const input=document.createElement('input');input.type='number';input.step='0.1';input.min=key==='radiusTop'?'0':'0.1';input.max='1000';
      input.setAttribute('aria-label',`${node.id} ${labels[key]}`); const [prop,index]=key.split('.'); input.value=index===undefined?node[prop]:node[prop][index];
      input.dataset.node=node.id;input.dataset.key=key;label.append(input);fields.append(label);
    }
    section.append(fields);host.append(section);
  }
}
function select(recipe) { draft=structuredClone(recipe); $('recipe').value=recipeText(draft); showParameters(draft); status('Recipe staged. Build to update the displayed model.'); }
function build(recipe, undoing = false) {
  if (busy) return;
  const id=++sequence;
  setBusy(true);status('Building locally on your device…');
  const w=restartWorker();
  timeout=setTimeout(()=>stop('Build stopped after 30 seconds. Previous model preserved; reduce complexity.'),30000);
  w.onerror=event=>stop(`The browser worker could not start or ran out of resources. ${event.message ?? ''} Try a simpler model or check that all app files are served. Previous model preserved.`);
  w.onmessage=({data})=>{
    if(data.id!==id)return;
    clearTimeout(timeout);w.terminate();setBusy(false);
    if(data.error){status(`Build rejected: ${data.error} Previous model preserved.`,true);return;}
    const geometry=new THREE.BufferGeometry(); geometry.setAttribute('position',new THREE.BufferAttribute(data.positions,3));geometry.setIndex(new THREE.BufferAttribute(data.indices,1));geometry.computeVertexNormals();
    const next=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color:0x168e87,metalness:.25,roughness:.36,flatShading:true}));
    if(undoing)history.pop();
    else if(built){history.push(structuredClone(built.recipe));if(history.length>20)history.shift();}
    if(mesh){scene.remove(mesh);mesh.geometry.dispose();mesh.material.dispose();}mesh=next;scene.add(mesh);
    built={recipe:structuredClone(recipe),report:data.report};draft=structuredClone(recipe);
    $('recipe').value=recipeText(recipe);showParameters(recipe);
    $('model-name').textContent=recipe.name;
    $('dimensions').textContent=data.report.dimensions.map(x=>x.toFixed(2)).join(' × ');
    $('volume').textContent=data.report.volume.toLocaleString(undefined,{maximumFractionDigits:2});
    $('triangles').textContent=data.report.triangles.toLocaleString();$('validity').textContent=data.report.closed?'Closed ✓':'Failed';
    $('build-note').textContent='Save a recipe to keep your work';
    const span=Math.max(...data.report.dimensions,1);grid.scale.setScalar(span/100);grid.position.z=data.report.bounds.min[2]-.02;
    fit(true);status('Built and checked: closed edges, consistent winding, positive mesh volume. Mesh checks are not engineering certification.');
    for(const key of ['stl','save','report'])$(key).disabled=false;setBusy(false);
  };
  w.postMessage({id,recipe});
}
function download(blob,name) {const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);}
async function copy(text) {try {await navigator.clipboard.writeText(text);status('Copied.');}catch {$('copy-text').value=text;$('copy-dialog').showModal();$('copy-text').select();}}
function safeName(){return (built.recipe.name.replace(/[^a-z0-9_-]+/gi,'-').slice(0,80)||'intact-part');}
$('flange').onclick=()=>{select(EXAMPLES.flange);build(draft);};
$('bracket').onclick=()=>{select(EXAMPLES.bracket);build(draft);};
$('box').onclick=()=>{select({format:'intact-browser-1',name:'Parametric box',units:'mm',nodes:[{id:'box',type:'box',size:[40,30,20]}],result:'box'});build(draft);};
$('build').onclick=()=>{try {build(parseRecipe($('recipe').value));}catch(e){status(`Recipe rejected: ${e.message} Previous model preserved.`,true);}};
$('apply').onclick=()=>{try {
  const candidate=structuredClone(draft);
  for(const input of $('parameters').querySelectorAll('input')){if(!input.checkValidity())throw new Error('Dimension fields must contain valid numbers.');const node=candidate.nodes.find(n=>n.id===input.dataset.node);const [prop,index]=input.dataset.key.split('.');if(index===undefined)node[prop]=Number(input.value);else node[prop][index]=Number(input.value);}
  build(parseRecipe(recipeText(candidate)));
}catch(e){status(e.message,true);}};
$('recipe').oninput=()=>status('Recipe edited. Build recipe to update geometry; exports still use the last successful build.');
$('cancel').onclick=()=>stop('Build cancelled. Previous model preserved.');
$('undo').onclick=()=>{if(busy||!history.length)return;build(history[history.length-1],true);};
$('fit').onclick=()=>fit();$('reset').onclick=()=>fit(true);$('bottom').onclick=()=>fit(false,true);
$('prompt').onclick=()=>copy(CHATGPT_PROMPT);
$('report').onclick=()=>copy(JSON.stringify({edition:'Intact Browser CAD 0.1.0',units:'mm',model:built.recipe.name,representation:'Polygonal mesh; not native B-rep or physical validation',...built.report},null,2));
$('save').onclick=()=>download(new Blob([recipeText(built.recipe)],{type:'application/json'}),`${safeName()}.intact.json`);
$('stl').onclick=()=>download(new Blob([new STLExporter().parse(mesh,{binary:true})],{type:'application/octet-stream'}),`${safeName()}.stl`);
$('import').onchange=async event=>{try{const file=event.target.files[0];if(!file)return;if(file.size>65536)throw new Error('Recipe exceeds 64 KiB.');select(parseRecipe(await file.text()));$('recipe').closest('details').open=true;}catch(e){status(e.message,true);}finally{event.target.value='';}};
$('close-copy').onclick=()=>$('copy-dialog').close();
document.addEventListener('keydown',event=>{if(['INPUT','TEXTAREA'].includes(document.activeElement.tagName)||event.ctrlKey||event.metaKey||event.altKey)return;if(event.key.toLowerCase()==='f')fit();if(event.key.toLowerCase()==='r')fit(true);});
try{initViewer();select(draft);build(draft);}catch(e){status(`3D startup failed: ${e.message}. This app requires WebGL, WebAssembly and modern browser support.`,true);$('loading').textContent='3D unavailable in this browser';for(const id of ['apply','build','flange','bracket','box'])$(id).disabled=true;}
