import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const root=path.dirname(fileURLToPath(import.meta.url));
await build({entryPoints:[path.join(root,'site/demo/demo-source.mjs')],bundle:true,minify:true,format:'iife',footer:{js:'/*\n'+fs.readFileSync(path.join(root,'THIRD_PARTY_LICENSES.txt'),'utf8').replaceAll('*/','* /')+'\n*/'},outfile:path.join(root,'site/demo/intact-demo.js')});
