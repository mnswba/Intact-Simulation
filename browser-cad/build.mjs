import {build} from 'esbuild';
import {mkdir,copyFile,writeFile,readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('.',import.meta.url));
process.chdir(root);
await mkdir('dist',{recursive:true});
await build({entryPoints:['app.mjs','worker.mjs'],outdir:'dist',entryNames:'[name]',bundle:true,format:'esm',platform:'browser',target:['safari16','chrome110','firefox115'],minify:true,external:['module','node:module']});
for(const name of ['index.html','app.css'])await copyFile(name,`dist/${name}`);
await copyFile('node_modules/manifold-3d/manifold.wasm','dist/manifold.wasm');
let notices='Intact Browser CAD 0.1.0\nOriginal Intact source: Apache-2.0.\n\n';
for(const [name,version,licensePath] of [['three','0.180.0','LICENSE'],['manifold-3d','3.3.2','LICENSE']]){
  notices+=`\n${name} ${version}\n`;
  try{notices+=await readFile(`node_modules/${name}/${licensePath}`,'utf8');}catch{throw new Error(`Missing license for ${name}; do not distribute without it.`);}
}
await writeFile('dist/THIRD_PARTY_NOTICES.txt',notices);
await copyFile('../LICENSE','dist/LICENSE.txt');
await copyFile('HOSTING.md','dist/HOSTING.md');
console.log('Static browser app built in browser-cad/dist. Serve over HTTPS; no CAD server or Node runtime needed on the host.');
