# Repository presentation assets

The README uses GitHub-compatible static PNG/SVG assets and an animated GIF. It does not depend on embedded JavaScript, autoplay video or animated SVG support.

- `hero.html` is the authored 1600 × 650 banner layout. Its CAD image is an actual viewer capture of the bundled six-hole flange.
- `../images/readme/workspace.png` captures Intact 0.20.0's Design workspace and Review panel using the public enclosure example.
- `../images/readme/assembly.gif` records display-only explosion of that example's two components. It does not depict AI generation, a solver run or a geometry edit.
- `../images/readme/architecture.svg` is an authored vector architecture diagram.
- `../images/readme/provenance.json` records the public source models and capture scope.

Example CAD was built through Intact's native isolated worker. Captures use a separate documentation library and `?snapshot=1`; no private user projects or sign-in context appear in these assets. The hero is rendered from the HTML layout after the flange capture is available. Readme assets are documentation media, not installation binaries or CAD runtime state.
