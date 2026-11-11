# Third-party notices

Original Intact source uses Apache-2.0. This does not change the license of third-party dependencies or vendored files.

- See [priority-1 inventory](docs/PRIORITY1_OPEN_SOURCE.md) for FreeCAD, OCCT, build123d, numerical and mesh components.
- See [priority-2/3 inventory](docs/PRIORITY23_OPEN_SOURCE.md) for Gmsh, scikit-fem, Manifold, meshio and ReportLab.
- Gmsh is GPL-licensed. FreeCAD/OCCT and bundled libraries retain their upstream notices and terms. Review upstream obligations before redistributing a combined runtime; this repository distributes adapter source rather than those binary runtimes.
- `vendor/shadcn-tailwind-4.13.0.*` retain their accompanying license.
- `scripts/vite/sites-vite-plugin.*` retain their accompanying license and notices.
- JavaScript and Python dependency packages retain the licenses distributed with their pinned versions.

The independently maintained https://github.com/earthtojake/text-to-cad is a reference for workflow and repository organization. It is not included as a submodule, does not own Intact's original source, and is not represented as endorsing this project. Any future imported upstream source must retain its actual copyright and license.

Project exports add python-pptx (MIT), ezdxf (MIT), and separately executed GNU LibreDWG 0.14 (GPL-3.0-or-later). LibreDWG is built from https://ftp.gnu.org/gnu/libredwg/libredwg-0.14.tar.xz with SHA256 `62ebb73b984f865960f20ed26619ea5f8789d5e3fd088fa40a2598384da81275`. The installer retains COPYING and source/download provenance; no LibreDWG binary is committed. Preserve its notices and applicable source obligations when redistributing the compiled tools.

USD/USDA exports use OpenUSD (`usd-core`, locked in backend/uv.lock). Preserve its upstream Apache-2.0 notices and bundled third-party license files. No USD runtime binaries are included in this Git repository.

Virtual Analysis uses PyBullet 3.2.7 from Bullet Physics (zlib license). Upstream source and license: https://github.com/bulletphysics/bullet3. The runtime is installed as a dependency; no PyBullet binaries are committed.
