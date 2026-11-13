// Data-only recipe interpreter. Never evaluate model text as JavaScript/Python.
export const LIMITS = Object.freeze({bytes: 65536, nodes: 64, segments: 128, dimension: 1000, position: 10000});
export function validateRecipe(value) {
  const fail = message => { throw new Error(message); };
  const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
  const keys = (v, allowed, label) => {
    if (!object(v)) fail(`${label} must be an object.`);
    for (const k of Object.keys(v)) if (!allowed.includes(k)) fail(`${label}: unsupported field ${k}.`);
  };
  keys(value, ['format', 'name', 'units', 'nodes', 'result'], 'Recipe');
  if (value.format !== 'intact-browser-1' || value.units !== 'mm') fail('Use format intact-browser-1 and units mm.');
  if (typeof value.name !== 'string' || !value.name.trim() || value.name.length > 80) fail('Name must contain 1–80 characters.');
  if (!Array.isArray(value.nodes) || !value.nodes.length || value.nodes.length > LIMITS.nodes) fail('Use 1–64 nodes.');
  const seen = new Set();
  const scalar = (n, key, min, max) => {
    if (typeof n[key] !== 'number' || !Number.isFinite(n[key]) || n[key] < min || n[key] > max) fail(`${n.id}: ${key} must be ${min}–${max}.`);
  };
  const vector = (v, min, max, label) => {
    if (!Array.isArray(v) || v.length !== 3 || v.some(x => typeof x !== 'number' || !Number.isFinite(x) || x < min || x > max)) fail(`${label} must contain three numbers from ${min} to ${max}.`);
  };
  for (const n of value.nodes) {
    if (!object(n) || typeof n.id !== 'string' || !/^[a-z][a-z0-9_-]{0,39}$/.test(n.id) || seen.has(n.id)) fail('Node IDs must be unique, lowercase names beginning with a letter.');
    const shapeKeys = {box: ['size'], cylinder: ['height', 'radius', 'radiusTop', 'segments'], sphere: ['radius', 'segments'], union: ['inputs'], subtract: ['inputs'], intersect: ['inputs']};
    if (!Object.hasOwn(shapeKeys, n.type)) fail(`${n.id}: unsupported type.`);
    keys(n, ['id', 'type', 'translate', 'rotate', ...shapeKeys[n.type]], n.id);
    if (n.translate !== undefined) vector(n.translate, -LIMITS.position, LIMITS.position, `${n.id} translate`);
    if (n.rotate !== undefined) vector(n.rotate, -360, 360, `${n.id} rotate`);
    if (n.type === 'box') vector(n.size, 0.1, LIMITS.dimension, `${n.id} size`);
    if (n.type === 'cylinder') {
      scalar(n, 'height', 0.1, LIMITS.dimension); scalar(n, 'radius', 0.1, LIMITS.dimension);
      if (n.radiusTop !== undefined) scalar(n, 'radiusTop', 0, LIMITS.dimension);
    }
    if (n.type === 'sphere') scalar(n, 'radius', 0.1, LIMITS.dimension);
    if (n.segments !== undefined && (!Number.isInteger(n.segments) || n.segments < 16 || n.segments > LIMITS.segments || n.segments % 4 !== 0)) fail(`${n.id}: segments must be a multiple of 4 from 16 to 128.`);
    if (['union', 'subtract', 'intersect'].includes(n.type)) {
      if (!Array.isArray(n.inputs) || n.inputs.length < 2 || n.inputs.length > 16 || n.inputs.some(id => typeof id !== 'string' || !seen.has(id))) fail(`${n.id}: use 2–16 input IDs defined earlier in the recipe.`);
    }
    seen.add(n.id);
  }
  if (!seen.has(value.result)) fail('Result must name an existing node.');
  return value;
}

export function parseRecipe(text) {
  if (new TextEncoder().encode(text).length > LIMITS.bytes) throw new Error('Recipe exceeds 64 KiB.');
  // Accept a single JSON markdown fence from chat, never arbitrary code.
  const source = text.trim().replace(/^```(?:json)?\s*\n([\s\S]*?)\n```$/, '$1');
  return validateRecipe(JSON.parse(source));
}

export function buildRecipe(api, recipe) {
  validateRecipe(recipe);
  const owned = new Set(), nodes = new Map();
  const keep = obj => { owned.add(obj); return obj; };
  const {Manifold} = api;
  try {
    for (const n of recipe.nodes) {
      let solid;
      if (n.type === 'box') solid = keep(Manifold.cube(n.size, true));
      else if (n.type === 'sphere') solid = keep(Manifold.sphere(n.radius, n.segments ?? 64));
      else if (n.type === 'cylinder') solid = keep(Manifold.cylinder(n.height, n.radius, n.radiusTop ?? n.radius, n.segments ?? 64, true));
      else {
        solid = nodes.get(n.inputs[0]);
        for (const id of n.inputs.slice(1)) {
          const method = {union: 'add', subtract: 'subtract', intersect: 'intersect'}[n.type];
          solid = keep(solid[method](nodes.get(id)));
        }
      }
      if (n.rotate) solid = keep(solid.rotate(n.rotate));
      if (n.translate) solid = keep(solid.translate(n.translate));
      if (solid.status() !== 'NoError') throw new Error(`${n.id}: kernel reported ${solid.status()}.`);
      nodes.set(n.id, solid);
    }
    const solid = nodes.get(recipe.result);
    if (solid.isEmpty()) throw new Error('Result is empty. Check dimensions, overlaps and Boolean inputs.');
    const mesh = solid.getMesh();
    if (mesh.triVerts.length / 3 > 250000) throw new Error('Result exceeds 250,000 triangles. Reduce detail.');
    const positions = new Float32Array(mesh.numVert * 3);
    for (let i = 0; i < mesh.numVert; i++) positions.set(mesh.vertProperties.subarray(i * mesh.numProp, i * mesh.numProp + 3), i * 3);
    const indices = new Uint32Array(mesh.triVerts);
    const bounds = solid.boundingBox();
    const audit = auditMesh(positions, indices);
    if (!audit.closed || !Number.isFinite(audit.volume) || audit.volume <= 0) throw new Error('Output mesh failed closed-edge/positive-volume checks.');
    return {positions, indices, report: {bounds, dimensions: bounds.max.map((x,i) => x - bounds.min[i]), volume: solid.volume(), area: solid.surfaceArea(), triangles: indices.length / 3, vertices: positions.length / 3, status: 'NoError', ...audit}};
  } finally {
    for (const obj of owned) obj.delete();
  }
}

export function auditMesh(positions, indices) {
  const edges = new Map(); let volume = 0;
  const origin = positions.subarray(0,3);
  for (let i = 0; i < indices.length; i += 3) {
    const ids = [indices[i], indices[i+1], indices[i+2]];
    // Translate the determinant near the mesh to avoid large-origin cancellation.
    const [a,b,c] = ids.map(j => [positions[j*3]-origin[0],positions[j*3+1]-origin[1],positions[j*3+2]-origin[2]]);
    volume += (a[0]*(b[1]*c[2]-b[2]*c[1]) + a[1]*(b[2]*c[0]-b[0]*c[2]) + a[2]*(b[0]*c[1]-b[1]*c[0])) / 6;
    for (let j = 0; j < 3; j++) {
      const u = ids[j], v = ids[(j+1)%3], key = `${Math.min(u,v)},${Math.max(u,v)}`;
      const edge = edges.get(key) ?? {count: 0, balance: 0}; edge.count++; edge.balance += u < v ? 1 : -1; edges.set(key, edge);
    }
  }
  return {closed: [...edges.values()].every(e => e.count === 2 && e.balance === 0), volume};
}

export const EXAMPLES = {
  flange: {format:'intact-browser-1', name:'Six-hole flange', units:'mm', nodes:[
    {id:'disk', type:'cylinder', height:8, radius:40, segments:96},
    {id:'bore', type:'cylinder', height:12, radius:12, segments:96},
    ...Array.from({length:6}, (_,i) => ({id:`hole${i}`,type:'cylinder',height:12,radius:3,segments:32,translate:[30*Math.cos(i*Math.PI/3),30*Math.sin(i*Math.PI/3),0]})),
    {id:'flange',type:'subtract',inputs:['disk','bore',...Array.from({length:6},(_,i)=>`hole${i}`)]}
  ],result:'flange'},
  bracket: {format:'intact-browser-1',name:'Mounting bracket',units:'mm',nodes:[
    {id:'foot',type:'box',size:[60,40,6]},
    {id:'wall',type:'box',size:[60,6,40],translate:[0,17,17]},
    {id:'body',type:'union',inputs:['foot','wall']},
    {id:'hole_a',type:'cylinder',height:10,radius:3,translate:[-20,-5,0]},
    {id:'hole_b',type:'cylinder',height:10,radius:3,translate:[20,-5,0]},
    {id:'bracket',type:'subtract',inputs:['body','hole_a','hole_b']}
  ],result:'bracket'}
};

export const CHATGPT_PROMPT = `Create a data-only JSON CAD recipe for Intact Browser CAD. Ask me for my part, dimensions and important constraints first. Then return one JSON code block, no JavaScript or Python. This is a polygonal mesh edition, not native STEP/FreeCAD, FEA or all 65 desktop tools. Only millimetres, right-handed Z-up. All primitives are centered. Rotations are XYZ degrees before translations. No scripts, URLs or expressions in values.
Schema: {"format":"intact-browser-1","name":"Part name","units":"mm","nodes":[...],"result":"last_node_id"}.
IDs: unique lowercase letter then lowercase letters/digits/underscore/hyphen, max40 chars. Max64 nodes. Each node: id,type, optional rotate:[x,y,z] (each -360..360) and translate:[x,y,z] (each -10000..10000).
Types: box size:[x,y,z]; cylinder height,radius,optional radiusTop (0 makes a cone), optional segments; sphere radius,optional segments; union/subtract/intersect inputs:[2..16 previously defined node IDs]. Subtract removes each later input from the first. Dimensions0.1..1000 mm. radiusTop0..1000. segments multiple4 between16and128, default64. No other keys. Use numerical literals only. All needed intermediate nodes must precede their use. Use simple Boolean combinations and avoid coincident cuts. No fillets, text, sweeps, imported files, arbitrary scripts, physical simulation or unsupported geometry. Explain limitations if a request cannot be represented. Hole cutters should extend beyond the body. After my approval I will paste the recipe into the browser and press Build. You cannot see or execute my browser model automatically; ask me to share the measured report when checking it.
Example:\n${JSON.stringify(EXAMPLES.flange)}`;
