# Intact Simulation WordPress website

Public site: https://www.intactsimulation.com/ · Architecture: https://www.intactsimulation.com/architecture/ · Tutorial: https://www.intactsimulation.com/how-to-use/

## Browser CAD preview

The separate [Browser CAD preview 0.1.0](https://www.intactsimulation.com/browser-cad/) is published on the existing WordPress host, page ID 210. Source, architecture and verification are in [`browser-cad/`](../browser-cad/README.md). It builds new primitive/Boolean meshes on the user's device, with manual ChatGPT recipe exchange, measured reports, editable JSON and STL. It introduces no publisher CAD server or API key. Full native 65-tool parity and direct ChatGPT tool integration are not claimed.

Build with `cd browser-cad && npm ci && npm run build`. Its self-contained `dist/wordpress-page.json` is the source payload for the admin-owned WordPress page; it embeds the app in an opaque-origin sandboxed iframe. `wordpress-host-preview.html` exercises that same embedding without WordPress. The static-directory deployment is also included. Generated runtime bytes remain outside Git. The WordPress app denies network connections from the embedded workspace; models are not uploaded. Live Chromium desktop and emulated phone/tablet checks passed, but real iOS/Android hardware validation is pending. `browser-publication.json` records actual publication separately from draft build output. Get Started links to the preview using `content/browser-cad-banner.html`.

## Windows download and private installation

The 0.20.0 Windows-Local ZIP is published as a versioned [GitHub release asset](https://github.com/mnswba/Intact-Simulation/releases/tag/v0.20.0). The website's [Get Started](https://www.intactsimulation.com/getting-started/) page, homepage and shared calls to action deliver that same file and explain private installation through Codex on another Windows computer. The WordPress binary upload timed out; no separate WordPress-hosted copy is claimed. `downloads.json` is the source of the public download URL, version, size and SHA-256.

All 18 existing content pages were published and their saved raw content checked against the prepared payload after HTML-entity normalization. The live Get Started button downloaded the correctly named ZIP and its SHA-256 matched the local package. Desktop (1440 px) and mobile (390 px) checks passed, including all five installation steps and no horizontal overflow. The GitHub release includes the ZIP, checksum, verification record and installation guide. See `download-publication.json` for the public verification receipt. This publication is software distribution, not OpenAI directory approval.

The November 13 content update was published through the authenticated WordPress REST API: 17 pages, including four new articles, returned HTTP 200 with the updated navigation. Submitted content matched WordPress's saved content after numeric HTML-entity normalization. Visual browser QA was not performed for this update. Credentials were not written into project files.

The update centers the installed ChatGPT plugin. The current Get Started page provides the native Windows 0.20.0 ZIP and a private Codex installation procedure for another computer. The homepage and shared calls to action link to the same versioned GitHub release asset, declared in `downloads.json`; a separate Open ChatGPT link remains for existing users. Opening ChatGPT does not install the plugin, and no public-directory approval or one-click installation URL is claimed. Source-code archives are distinct from the Windows-Local plugin package. Source-code navigation remains absent from marketing navigation; dependency attribution remains.

Architecture contains an accessible HTML/CSS system map, an ordered modeling and repair flow, the engineering stack and an explanation of geometry audits versus design verification and physical validation. How to Use covers the viewer workflows and generates its shortcut table directly from `scripts/viewer/shortcuts.mjs`. The existing `/how-it-works/` page remains a tutorial alias to preserve bookmarks; its existing WordPress page ID should be updated rather than deleted. Architecture and How to Use are new page slugs. Contact includes URDT's official company reference and the project owner's supplied developer biography. The article collection now contains eight practical engineering guides.

Content lives in `content/`, shared additions in `content.css`, and page generation in `build_wordpress.py`. Build output remains draft payloads until an authenticated WordPress publisher explicitly applies the update. Do not treat a local build as a production deployment.

The website is published on the user's existing WordPress installation. The prepared update has a responsive product layout, architecture and user-tutorial pages, plugin setup, eight technical articles, a searchable Finished Work collection, company/contact information and a factual data-flow page. The interactive examples remain available. `site-map.json` records the existing public content IDs; `public-assets.json` contains only public media URLs. The contact email was already displayed publicly on the original site.

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

## Industry expansion and prompt provenance

The collection now contains 50 models in ten groups. The newest 30 industry assemblies have 1,072 native named parts, exact design prompts recorded before source creation and 2,324 passed export audit checks. Gallery cards and demo sidebars expose each prompt; new ZIPs include `design-prompt.txt` and `geometry-audit.json`. Original examples have clearly labelled reconstructed briefs rather than invented verbatim transcripts. All 30 public packages were checksum-matched to their originals and checked for native export signatures, exact prompts and audit results. Production Chromium checked model dimensions/component counts, prompt text, category/search/reset/copy behavior and mobile width. The recorded original four browser examples also passed regression checks.
