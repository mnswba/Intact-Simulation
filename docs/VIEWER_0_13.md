# Viewer workspace — 0.13.0

This release adds the requested eight workflows to the local CAD viewer:

1. The parameter disclosure is named **Parameters (mm)**. Length values use CAD millimeters; counts, ratios and named angle parameters retain their own meaning.
2. **Full screen** replaces the header Assembly button. It shows the viewport and a **Compact screen** exit. Escape restores the workspace. A viewport-only CSS layout still works when the host declines native browser fullscreen.
3. Right-click model geometry or a component/face/edge in the navigator for selected-parent-part hide/isolation, Show all, Ask AI, native dimensions, snapped measurement mode, color and zoom-to-fit. Color edits remain disabled in revision previews. Right-button pan does not accidentally create selections or dimensions.
4. **Project** replaces the direct PNG button. Its submenu creates annotated viewport PNG, a multi-view PowerPoint deck, BOM CSV, 2D DXF/DWG drawings and project JSON. Exports bind to the requested revision/artifact and preserve the CAD revision.
5. Zoom-to-fit sits beside Grid. Dedicated Zoom +/− buttons are omitted; the mouse wheel zooms both perspective and orthographic cameras.
6. Projection includes perspective, orthographic, top, bottom, front, back, both sides and isometric views.
7. New text notes attach to the clicked model surface using part identity, CAD XYZ and artifact identity. They follow orbit, pan, zoom, orientation and explosion, survive reload, and can be moved to another surface. Other sketch tools remain screen-space references. Legacy text can be reattached with Move. Geometry rebuilds clear stale annotation anchors rather than guessing new faces.
8. **Add name** replaces the old Fit model button in Section & assembly. Visible part names follow exploded component positions with leader lines; the same labels appear in PNG/deck captures. The button toggles to Hide names. Fit remains available beside Grid and in the context menu.

Files & exports contains STEP, ASCII STL, Binary STL, GLB, 3MF, Python, Project JSON, USD and USDA. Native FreeCAD/source STEP documents remain available conditionally in Project. USD is a binary OpenUSD scene; USDA is its readable text counterpart. Both carry tessellated assembled geometry, named parts, transforms, colors, Z-up and millimeter scale. ASCII and binary STL are distinct validated encodings. The existing export_model AI tool accepts the new formats; the public tool count stays 53.

Tutorial sits immediately after Settings. It offers 107 searchable topics with names, definitions and usage steps, plus a guided-tour toggle, topic picker, Previous/Next, highlighting and panel restoration. It opens controls without running CAD edits, AI or exports. Escape and Close end the tour.

The compact component/history behavior from 0.12.2 remains: collapsed components, the current model pinned above four recent models, and no manual Requirements / Feature history / Engineering jobs panels. The engine retains useful CAD/verification/simulation tools, with 53 public MCP tools.

## File scope

- PPTX: six slides by default: title/revision, current viewport, isometric/top/front captures and saved component measurements. Camera position, orthographic frustum/zoom and display settings are restored after capture.
- BOM: one row per saved named instance with quantity 1, assigned material, CAD bounds, volume and area. It includes display-hidden components. It is not a grouped supplier/pricing catalog. Formula-like cell text is escaped for spreadsheet import.
- DXF/DWG: front/top/right wireframe projections of native edge samples, in millimeters. Curves are polylines. Hidden-line removal, manufacturing dimensions and 3D DWG solids are not provided. Triangle-only geometry must use its mesh/export workflows. DWG uses separately installed GNU LibreDWG 0.14, writes R2000 and validates read-back; a specific external CAD application's compatibility remains untested.

The installer prepares locked python-pptx/ezdxf dependencies and SHA256-pinned GNU LibreDWG source. Runtime binaries, user geometry, export files and auth data remain outside the GitHub source checkout. Third-party licenses and source provenance are documented in THIRD_PARTY_NOTICES.md.

## Validation

44 targeted backend tests passed in batches (10 + 17 + 17), including real BOM/PPTX/DXF/DWG output, DWG read-back, revision/origin/path guards, anchor validation and retained CAD/AI workflows. 31 JavaScript tests passed. The workspace tests cover 22 browser groups; the export/tutorial tests additionally exercise all nine real downloads and every one of 107 tutorial topics, with guided/off/search/restore/mobile checks. The installed audit passed 50 browser workflow groups: 22 workspace, 11 export/tutorial, 9 navigation and 8 Ask AI, including traversal of all 107 tutorial topics. Actual exported PPTX was reopened and verified to contain six slides and four viewport images.

Browser checks use Chromium. The browser-native annotation bridge is simulated for the Ask AI contract; the actual Windows ChatGPT annotation editor and third-party DWG applications were not automated. Evidence stays locally under ignored outputs/workspace-audit, outputs/navigation-audit and outputs/chat-handoff-audit. User projects were not used as test fixtures.
