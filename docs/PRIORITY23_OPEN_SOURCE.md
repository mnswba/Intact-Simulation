# Priority 2/3 open-source runtime

The original Intact adapters in `advanced.py`, `advanced_mcp.py`, `advanced_worker.py`, `simulation_worker.py`, `p23_schema.py`, `engineering_jobs.py`, `component_library.py`, the added lattice helpers and engineering viewer module use Apache-2.0 SPDX notices and the included Apache license. Third-party licenses remain their own.

| Component | Pinned version | Purpose | Upstream license |
| --- | --- | --- | --- |
| Manifold Python | 3.3.2 | Double-precision closed mesh booleans | Apache-2.0 |
| Gmsh | 4.15.0 | Native STEP tetrahedral meshing | GPL-2.0-or-later; upstream license applies |
| scikit-fem | 12.0.2 | Sparse tetrahedral finite-element assembly | BSD-3-Clause |
| meshio | 5.3.5 | VTU results | MIT |
| ReportLab | 4.4.9 | Reference drawing PDFs | BSD |
| Existing SciPy / NumPy / scikit-image / trimesh | uv.lock | Distance fields, sparse algebra, silhouette extraction and mesh handling | Existing upstream notices |

FreeCAD/OCCT/build123d remain as listed in PRIORITY1_OPEN_SOURCE.md. Gmsh and OCP are kept in separate worker roles to avoid mixing their OCCT runtimes. Model-authored Python still executes only inside the existing sandbox.

The installer prepares required GL runtime libraries from the already checksum-verified FreeCAD bundle. libXft is extracted without root from Ubuntu's `libxft2_2.3.4-1_amd64.deb`, SHA256 `2f1f300e21c97023e0a8418d68e5eba095d2c5872ceab740f5d70278d94284fd`; its copyright notice and download provenance are retained. Python wheels retain their distributed license files. Preserve GPL/source obligations and all upstream notices when redistributing this runtime; the adapter's Apache notice does not relicense Gmsh.

Catalog dimensions are nominal geometric facts, attributed to FreeCAD Fasteners' ISO4762 table and the linked SKF608 datasheet. No supplier STEP assets, manufacturer logos or proprietary catalogs are bundled. Simplifications are explicit; these envelopes are not production drawings or evidence of fits/ratings.
