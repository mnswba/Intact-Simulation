import Module from 'manifold-3d';
import {buildRecipe} from './core.mjs';
const ready = Module({
  wasmBinary: typeof INTACT_WASM_BASE64 === 'undefined' ? undefined : Uint8Array.from(atob(INTACT_WASM_BASE64), c => c.charCodeAt(0)),
  locateFile: name => typeof INTACT_WASM_BASE64 === 'undefined' ? new URL(name, self.location.href).href : name
}).then(api => {api.setup(); return api;});
self.onmessage = async ({data}) => {
  try {
    const result = buildRecipe(await ready, data.recipe);
    self.postMessage({id: data.id, ...result}, [result.positions.buffer, result.indices.buffer]);
  } catch (e) {self.postMessage({id:data.id, error:String(e.message ?? e)});}
};
