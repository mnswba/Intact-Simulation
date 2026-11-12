# Intact Simulation 0.16.1

The CAD viewer now embeds the Intact mark directly in its header, removing the separate SVG image request. The constrained-sketch draft viewer also displays the logo; its previous capitalized text header had been missed. Both viewers have an explicit PNG favicon. Header marks have an accessible name and a fixed 40 × 40 px size.

Portable and compatibility manifests now reference bundled 256 px PNG listing icons. The bundled skill has its own display name, description and 64/256 px icon metadata, which is separate from plugin listing metadata. SVG masters remain available. These PNGs are browser exports of the authored vector logo; no third-party brand assets were added.

Verification: installed solid and draft viewers render the logo at 1400 px and 480 px widths in light/dark themes, including with external SVG loading blocked. The favicon endpoint returns a valid PNG. All six active installed plugin copies contain the referenced icons and skill metadata. Native ChatGPT plugin-list rendering was not automated; a client restart loads new listing metadata. User CAD and saved revision records are preserved.

The [launch guide](CHATGPT_LAUNCH.md) now explicitly distinguishes individual identity verification from the separate partner/allowlisting requirement for local desktop plugins. An individual engineer can submit under a verified personal name; GitHub ownership alone does not establish directory eligibility or approval.
