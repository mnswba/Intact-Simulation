import {build} from 'esbuild';
await build({entryPoints:['scripts/plugin-viewer.mjs'],bundle:true,minify:true,format:'esm',outfile:'backend/intact_backend/viewer.js'});
await build({entryPoints:['scripts/draft-viewer.mjs'],bundle:true,minify:true,format:'esm',outfile:'backend/intact_backend/draft_viewer.js'});
