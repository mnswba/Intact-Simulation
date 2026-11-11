# Priority 1 open-source inventory

The new tools use open-source CAD components. ChatGPT remains the selected conversational AI; it is not an open-source model and is not bundled or retrained by Intact.

| Component | Use | License / source |
| --- | --- | --- |
| FreeCAD 1.1.4 official Linux Python 3.11 AppImage | Real sketch constraint solver, Part/PartDesign feature steps, native FCStd and STEP generation | [FreeCAD licensing](https://github.com/FreeCAD/FreeCAD/blob/main/LICENSE); bundled third-party notices remain intact |
| build123d 0.13 | Existing native CAD/program execution, export and inspection | [Apache 2.0](https://github.com/gumyr/build123d/blob/dev/LICENSE) |
| CadQuery OCP bindings | Python access to native geometry | [Apache 2.0 wrapper](https://github.com/CadQuery/OCP/blob/master/LICENSE) |
| OpenCASCADE kernel | Geometry, topology, intersections and distances | [LGPL 2.1 with Open CASCADE exception](https://dev.opencascade.org/doc/overview/html/occt_public_license.html) |
| Pydantic | Strict typed schemas and argument validation | [MIT](https://github.com/pydantic/pydantic/blob/main/LICENSE) |
| Existing NumPy, trimesh and Three.js stack | Mesh convergence measurements and viewport | Existing upstream licenses remain applicable |

The official FreeCAD asset is `FreeCAD_1.1.4-Linux-x86_64-py311.AppImage`, pinned SHA256 `f6dc6ba676e5ac96a565ebc8d657232f94c6158e85b4352141bd1a46f6b43434`. The installer verifies the complete download and extracts it without root. Installation metadata records the official URL and digest in the runtime directory. It does not install a proprietary CAD engine or add-on.

The original Intact adapter code introduced for priority 1 is supplied under Apache-2.0, as marked by its SPDX headers and `LICENSE-PRIORITY1.txt`. This applies to the new backend files `engineering_schema.py`, `isolated_worker.py`, `freecad_worker.py`, `feature_graph.py`, `stable_references.py`, `native_checks_worker.py`, `design_checks.py`, `feature_source.py`, `accuracy.py`, the new engineering/draft viewer modules, and the FreeCAD installer. It does not relicense third-party software or unrelated existing project code. Preserve upstream license and distribution notices when packaging the software.

The FreeCAD worker receives validated JSON and executes trusted adapter code in a separate bubblewrap sandbox. It cannot access the user's actual home, authentication files or network. A synthetic passwd entry supplies the isolated worker home required by FreeCAD. Python/OCCT libraries from the FreeCAD bundle are not imported into Intact's existing server process.

The 0.11 `ask_ai.py` adapter is original Apache-2.0 code. It invokes the installed OpenAI local client with its existing sign-in and a model-scoped MCP server; OpenAI inference and the user account are not open-source CAD components. No authentication files are copied or bundled.
