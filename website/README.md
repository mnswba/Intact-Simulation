# Intact Simulation WordPress website

Public site: https://www.intactsimulation.com/ · Demo: https://www.intactsimulation.com/demo/

The website is published on the user's existing WordPress installation. It has an original responsive product layout, an interactive demo, how-it-works and installation pages, four technical articles, a searchable Finished Work collection, contact links and a factual data-flow page. `site-map.json` records the public content IDs; `public-assets.json` contains only public media URLs. The contact email was already displayed publicly on the original site.

The browser demo uses actual authored example CAD and a recorded 1000 N compression result. It supports orbit/pan/zoom, standard views, grid, wireframe, sectioning, component visibility/isolation/color, enclosure explosion, native example downloads and recorded FEM field/deformation controls. It does not perform new AI generation or solve new analyses online. Custom generation and supported new studies require the local desktop plugin and CAD runtime.

## Rebuild locally

Install the root repository's Node dependencies first. Then, from the repository root:

```bash
node website/build-demo.mjs
python3 website/fetch-examples.py
python3 website/build_wordpress.py
python3 -m http.server 8766 --directory website/site
```

Open http://localhost:8766/. Generated previews, example binary downloads, WordPress payloads and compiled JS are ignored. The public example ZIPs contain native exports; they are loaded with the MIT-licensed fflate decoder bundled with Three.js. A gyroid is a sampled mesh, so its demo intentionally has no smooth STEP export.

## WordPress deployment

`build_wordpress.py` emits draft REST payloads in `website/wordpress/`. It does not authenticate, publish or contain credentials. Existing pages use the Extendable theme's `blank` template to avoid duplicate theme chrome. Review content before changing its status and publishing through WordPress's REST API or editor. Set article pages' parent to the articles index ID from `site-map.json`. Publish new supporting pages before updating the existing homepage.

The media policy blocks standalone `.js`, `.css` and `.glb` uploads. The demo therefore loads ordinary ZIP media and unpacks its own known example files in the browser. Display-only transformations never alter the native downloads. Its inline JS bundle is encoded to preserve exact bytes through WordPress formatting and then decoded into a script element; credentials are never included in that bundle. No security settings or upload MIME allowlists were weakened.

The current application password was used only in a temporary authenticated process and was not saved to the repository or generated site. Original site content/settings backups were retained outside the repository. Keep application passwords, backup settings, identity documents and private CAD out of version control and public uploads.

## Verification and scope

Local and production Chromium checks covered four examples, native/CSV downloads, sectioning, projection/wireframe/grid, component isolation/explosion, real recorded fields, mobile layout and navigation. The reference compression case uses a 10 × 10 × 20 mm block, E=10 GPa, nu=0, bottom fixed and 1000 N downward on top: displacement 0.020 mm, peak element-average von Mises stress 10 MPa and reaction +1000 N Z. This is not a whole-vehicle/contact analysis or certification.

Three.js and its bundled fflate decoder retain their MIT licenses. Original website content/source follows the repository license. No competitor code, copy, customer claims or founder identities were imported. Live hosting, authentication and per-user compute isolation for an online AI CAD service remain a separate implementation.

## Twenty-model Finished Work collection

The additional collection contains five robotics, five powertrain, five product and five TPMS concepts. Sources are under `models/showcase`; measured public metadata, parameters, media URLs and download formats are in `content/showcase.json`. Rebuild packages with the installed CAD-runtime Python using `python website/build-showcase.py --state-dir /tmp/intact-showcase-rebuild`. All geometry executes through the existing Linux sandbox. Thumbnails must be rendered from actual exported geometry and visually reviewed. Native concepts provide STEP; sampled TPMS provide GLB/STL/3MF.

The demo now keeps each CAD part as a component even when glTF splits its mesh into several material primitives, preserves original part colors, computes missing mesh normals, and adapts native/mesh glTF coordinates consistently. All 20 public models were loaded in Chromium and checked against actual part counts and measured dimensions. All 20 public ZIPs matched their original SHA-256 checksums; native export signatures were inspected. The production gallery passed category/search/empty/reset and mobile-width checks. These are geometry examples, not model retraining or certified designs.
