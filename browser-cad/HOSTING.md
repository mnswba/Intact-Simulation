# Intact Browser CAD preview 0.1.0

This is a separate, reduced browser edition. It does not update or replace Windows plugin 0.20.0 and is not a ChatGPT public-directory submission package.

## Publish using the existing website

1. Build with Node 22+: `cd browser-cad`, `npm ci`, `npm run build`.
2. Upload **the contents of `dist/`** together to a static directory on the existing WordPress web host, for example `public_html/browser-cad/`. Use your hosting control panel file manager or SFTP. Uploading a ZIP as a WordPress Media Library attachment does not deploy the application.
3. Serve `index.html`, `app.js`, `worker.js`, `manifold.wasm`, `app.css`, the licenses and this guide at the same directory URL over HTTPS. Required types: `.js` JavaScript, `.wasm` `application/wasm`, `.css` `text/css`. The app must not inherit a policy that blocks same-origin workers or WebAssembly. It does not need cross-origin isolation, database access, PHP execution, an API key or a computation server.
4. Visit the directory URL, build the flange, then the bracket. Verify downloading STL and saving/opening recipe JSON. Confirm no 404s for WASM or worker assets. Test on real target phones and tablets before advertising device support.
5. Link the verified URL from Get Started. Do not advertise an unverified guessed URL. Keep the native Windows download for the full feature set.

For development: from `dist/` run `python -m http.server 8765 --bind 127.0.0.1`, then open `http://127.0.0.1:8765`. Do not double-click index.html: file URLs cannot load the worker/runtime reliably. A localhost server on your laptop is not a public mobile deployment.

## Use with ChatGPT

1. Open the app. Try an example and inspect the model.
2. Open **Design with ChatGPT**, copy the instructions, and paste them into your own ChatGPT conversation. Tell ChatGPT the dimensions and purpose of your part.
3. Copy the returned JSON recipe into **Model recipe**, then click **Build recipe**. No automatic tool connection or host approval is implied.
4. Inspect the actual model and measured envelope/volume. Adjust dimensions in the form or edit the recipe. For a review, copy the measured report back to ChatGPT; ChatGPT cannot automatically inspect this browser tab.
5. Save the recipe for editable geometry and export STL for mesh tools. STL has no unit field: import in millimetres. Temporary browser memory is not a persistent project library.

Supported geometry: centered boxes, cylinders/cones, spheres; ordered union/subtraction/intersection; XYZ rotations in degrees and translations in millimetres. Max64 nodes, 64KiB recipe, 128 circular segments, 250000 output triangles, 30-second worker deadline. Budget exhaustion preserves the last successful model. Generated scripts are never executed. Polygonal curves are approximations; there is no native STEP, full FreeCAD sketch solver, FEA, imported mesh support or desktop 65-tool parity.

Models are processed on-device and not uploaded by the app. Website asset requests still reach the web host; anything copied into ChatGPT follows ChatGPT's own data handling. No browser autosave or analytics is included. GPU/browser bugs and OS memory limits remain outside the worker deadline guarantee.

## Device status

Requires modern WebAssembly, WebGL, module workers, JavaScript and browser downloads. Desktop Chromium and emulated mobile viewport testing can check responsive behavior, not establish real iOS Safari or Android hardware support. See the repository browser-cad/README.md for actual verification results. Unsupported/restricted devices may fail gracefully; this is not an any-device guarantee.
