export type Kind = 'beam' | 'fin' | 'plate' | 'heatsink' | 'box_shell' | 'custom';
export type MaterialId = 'aluminum' | 'steel' | 'copper';
export type Design = { name: string; kind: Kind; length: number; width: number; height: number; holeDiameter: number; finCount: number; material: MaterialId; wall?: number; measuredVolume?: number };
export const materials = {
  aluminum: { name: 'Aluminum 6061-T6', E: 68.9e9, k: 167, density: 2700, yield: 276e6 },
  steel: { name: 'Steel · representative', E: 200e9, k: 50, density: 7850, yield: 250e6 },
  copper: { name: 'Copper · representative', E: 117e9, k: 391, density: 8960, yield: 70e6 },
};
export const presets: Record<Exclude<Kind,'custom'>, Design> = {
  box_shell: { name: 'Electronics enclosure', kind: 'box_shell', length: 160, width: 100, height: 50, wall: 3, holeDiameter: 6, finCount: 9, material: 'aluminum' },
  heatsink: { name: 'Parallel-fin heat sink', kind: 'heatsink', length: 100, width: 80, height: 35, holeDiameter: 6, finCount: 9, material: 'aluminum' },
  beam: { name: 'Cantilever study', kind: 'beam', length: 180, width: 30, height: 8, holeDiameter: 6, finCount: 9, material: 'aluminum' },
  fin: { name: 'Rectangular cooling fin', kind: 'fin', length: 80, width: 40, height: 3, holeDiameter: 6, finCount: 9, material: 'aluminum' },
  plate: { name: 'Four-hole mounting plate', kind: 'plate', length: 100, width: 70, height: 6, holeDiameter: 8, finCount: 9, material: 'aluminum' },
};
export function validateDesign(value: unknown): Design {
  if (!value || typeof value !== 'object') throw new Error('The project must contain a design.');
  const d = value as Design;
  if (!(d.kind==='custom'||Object.keys(presets).includes(d.kind)) || !(Object.keys(materials).includes(d.material))) throw new Error('Unsupported shape or material.');
  for (const key of ['length','width','height'] as const) if (!Number.isFinite(d[key]) || d[key] < (d.kind==='custom'?1e-6:1) || d[key] > (d.kind==='custom'?1e6:1000)) throw new Error('Dimensions must be between 1 and 1,000 mm.');
  if (!Number.isFinite(d.holeDiameter) || d.holeDiameter < .1 || d.holeDiameter > 250 || (d.kind==='plate' && (d.holeDiameter<1 || d.holeDiameter > Math.min(d.length, d.width) / 4))) throw new Error('Hole diameter must be between 1 mm and one quarter of the smaller plate dimension.');
  if (!Number.isInteger(d.finCount) || d.finCount < 3 || d.finCount > 30) throw new Error('Choose between 3 and 30 fins.');
  if (d.kind === 'heatsink' && (d.height < 8 || d.width < d.finCount * 2)) throw new Error('A heat sink needs at least 8 mm height and enough width for 2 mm per fin.');
  if (d.kind === 'box_shell' && (!Number.isFinite(d.wall ?? 3) || (d.wall ?? 3) < .5 || (d.wall ?? 3) > 100 || 2*(d.wall ?? 3)>=Math.min(d.length,d.width) || (d.wall ?? 3)>=d.height)) throw new Error('Wall thickness must leave a positive enclosure cavity.');
  if (typeof d.name !== 'string' || d.name.length < 1 || d.name.length > 100) throw new Error('Project names must be 1–100 characters.');
  return { name: d.name, kind: d.kind, length: d.length, width: d.width, height: d.height, holeDiameter: d.holeDiameter, finCount: d.finCount, material: d.material, ...(d.kind==='box_shell'?{wall:d.wall??3}:{}),...(d.kind==='custom'?{measuredVolume:d.measuredVolume}:{}) };
}
export function volume(d: Design) {
  if(d.kind==='custom')return d.measuredVolume??0;
  if (d.kind === 'box_shell') {const w=d.wall??3;return d.length*d.width*d.height-(d.length-2*w)*(d.width-2*w)*(d.height-w);}
  if (d.kind === 'plate') return d.length*d.width*d.height - 4*Math.PI*(d.holeDiameter/2)**2*d.height;
  if (d.kind === 'heatsink') return d.length*d.width*4 + d.finCount*d.length*1.5*(d.height-4);
  return d.length*d.width*d.height;
}
export type GuidedResult = { design: Design; message: string };
export function guidedDesign(text: string, current: Design): GuidedResult {
  const t = text.toLowerCase().trim();
  // Restricted, explicit commands. This parser is deliberately not represented as an AI model.
  let kind: Exclude<Kind,"custom"> | undefined;
  if (/enclosure|box shell/.test(t)) kind='box_shell'; else if (/heat\s*sink/.test(t)) kind='heatsink'; else if (/\bplate\b/.test(t)) kind='plate'; else if (/\bfin\b/.test(t)) kind='fin'; else if (/\bbeam\b|cantilever/.test(t)) kind='beam';
  const d = { ...(kind && kind !== current.kind ? presets[kind] : current) };
  const dims = t.match(/(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)(?:\s*mm)?/);
  let changed = !!kind;
  if (dims) { d.length=+dims[1]; d.width=+dims[2]; d.height=+dims[3]; changed=true; }
  for (const key of ['length','width','height'] as const) {
    const m=t.match(new RegExp('\\b'+key+'\\s*(?:to|=|:)??\\s*(\\d+(?:\\.\\d+)?)\\s*(?:mm)?'));
    if (m) { d[key]=+m[1]; changed=true; }
  }
  const wall=t.match(/wall(?:s| thickness)?\s*(?:to|=|:)?\s*(\d+(?:\.\d+)?)/);if(wall){d.wall=+wall[1];changed=true;}
  const fins=t.match(/(\d+)\s*fins\b/); if (fins) { d.finCount=+fins[1];changed=true; }
  const hole=t.match(/holes?\s*(?:diameter|of|=|:)?\s*(\d+(?:\.\d+)?)/);if(hole){d.holeDiameter=+hole[1];changed=true;}
  for(const m of Object.keys(materials) as MaterialId[]) if(t.includes(m)){d.material=m;changed=true;}
  if (!changed) throw new Error('Guided mode supports beam, plate, fin, heat sink or enclosure; dimensions such as 180 × 30 × 8 mm; named dimensions; aluminum, steel or copper. General AI design is available through the Intact Simulation plugin in ChatGPT.');
  // Irrelevant hole defaults must not block narrow fins.
  if (d.kind !== 'plate') d.holeDiameter=Math.min(d.holeDiameter,Math.min(d.length,d.width)/4);
  const checked=validateDesign(d);
  return { design: checked, message: `Updated ${checked.name.toLowerCase()}: ${checked.length} × ${checked.width} × ${checked.height} mm, ${materials[checked.material].name}. This was generated with the guided template builder.` };
}
