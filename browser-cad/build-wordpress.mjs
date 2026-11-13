// Produce a self-contained isolated iframe for an existing admin-owned WP page.
// All runtime bytes ship with the page: no model requests or remote CAD service.
import {build} from 'esbuild';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
process.chdir(fileURLToPath(new URL('.',import.meta.url)));
const escape=s=>s.replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const wasm=(await readFile('dist/manifold.wasm')).toString('base64');
const worker=await build({entryPoints:['worker.mjs'],bundle:true,format:'iife',platform:'browser',target:'es2022',minify:true,write:false,external:['module'],define:{INTACT_WASM_BASE64:JSON.stringify(wasm),'import.meta.url':JSON.stringify('https://intact.invalid/embedded-worker.js')}});
const app=await build({entryPoints:['app.mjs'],bundle:true,format:'esm',platform:'browser',target:'es2022',minify:true,write:false,define:{INTACT_WORKER_SOURCE:JSON.stringify(worker.outputFiles[0].text)}});
const script=app.outputFiles[0].text.replaceAll('</script','<\\/script');
let html=await readFile('index.html','utf8');
// Manifold's trusted Embind bindings construct JS call wrappers internally.
// Recipe data never enters these wrappers or an evaluator. No network permitted.
html=html.replace(/<meta http-equiv="Content-Security-Policy"[^>]*>/,'<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'unsafe-inline\' \'unsafe-eval\' blob: \'wasm-unsafe-eval\'; worker-src blob:; style-src \'unsafe-inline\'; img-src data: blob:; connect-src \'none\'; object-src \'none\'; base-uri \'none\'; form-action \'none\'">');
html=html.replace('<link rel="stylesheet" href="app.css">',`<style>${await readFile('app.css','utf8')}</style>`);
const notices=await readFile('dist/THIRD_PARTY_NOTICES.txt','utf8');
html=html.replace('<a href="THIRD_PARTY_NOTICES.txt">Open-source notices</a>',`<details><summary>Open-source notices</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere;font-size:10px">${escape(notices)}</pre></details>`);
html=html.replace('<script type="module" src="app.js"></script>',()=>`<script type="module">${script}</script>`);
await writeFile('dist/wordpress-preview.html',html);
const frame=`<style>html,body{margin:0!important;padding:0!important}.wp-site-blocks{padding:0!important}.wp-site-blocks>header,.wp-site-blocks>footer{display:none!important}.wp-block-post-content{max-width:none!important;margin:0!important}.wp-block-post-content>*{max-width:none!important}#intact-browser-frame{display:block;width:100%;height:100dvh;min-height:700px;border:0}</style><iframe id="intact-browser-frame" title="Intact Browser CAD preview" sandbox="allow-scripts allow-downloads allow-popups allow-popups-to-escape-sandbox" srcdoc="${escape(html)}"></iframe>`;
const payload={title:'Intact Browser CAD · Preview',slug:'browser-cad',status:'draft',content:`<!-- wp:html -->\n${frame}\n<!-- /wp:html -->`};
await writeFile('dist/wordpress-page.json',JSON.stringify(payload));
await mkdir('../website/wordpress',{recursive:true});
await writeFile('../website/wordpress/browser-cad.json',JSON.stringify(payload));
await writeFile('dist/wordpress-host-preview.html',`<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Intact Browser CAD host preview</title></head><body>${frame}</body></html>`);
console.log('Created WordPress draft payload and sandboxed iframe preview; publication is a separate step.');
