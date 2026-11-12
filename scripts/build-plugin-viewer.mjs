import {readFileSync} from 'node:fs';
import {build} from 'esbuild';
const version=readFileSync(new URL('../VERSION',import.meta.url),'utf8').trim();
await build({define:{__INTACT_VERSION__:JSON.stringify(version)},entryPoints:['scripts/plugin-viewer.mjs'],bundle:true,minify:true,format:'esm',outfile:'backend/intact_backend/viewer.js'});
await build({entryPoints:['scripts/draft-viewer.mjs'],bundle:true,minify:true,format:'esm',outfile:'backend/intact_backend/draft_viewer.js'});
