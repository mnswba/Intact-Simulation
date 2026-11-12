# Intact Simulation in ChatGPT · 0.16.0

The plugin name is **Intact Simulation**, ID `intact-simulation`. It supplies local MCP CAD and numerical tools, a viewer and a bundled skill. ChatGPT supplies reasoning. There is no LiteLLM or extra model-service API key.

Install inside Linux/WSL with `python3 scripts/install-chatgpt-plugin.py --windows-home /mnt/c/Users/YOUR_WINDOWS_USER`. Restart ChatGPT desktop and enable Intact in your personal plugin marketplace. The installer preserves other plugins, user CAD and revisions. Native Windows/macOS execution is not currently supported.

Ask ChatGPT to build and verify a model, then open its viewer. Select geometry, describe the change and click Ask AI. This automatically sends through a supported ChatGPT component bridge when present; the top-level localhost viewer otherwise starts a separate task through the signed-in local OpenAI client. Its progress, answers and replies appear in Intact. The fallback does not join the open ChatGPT conversation. No Annotation editor or copy/paste step is needed. See [delivery details](ASK_AI_HANDOFF.md).

Mechanical Analysis has a single Ask AI button. Specify material, supports, loaded component/faces and force/temperature/flow inputs. AI configures and runs the supported solver, and the viewer shows actual result fields, convergence and downloadable data. Missing physical inputs require a clarification. The 3D solver supports single-solid small-strain elasticity, steady conduction and bounded creeping-flow Stokes; it does not implement whole-assembly contact, nonlinear stress or turbulent CFD. Virtual Analysis provides prescribed kinematic previews, not dynamics.

Historical revisions are read-only previews. STEP preserves native solids; sampled/faceted TPMS exports are explicitly labeled. A source checkout or private installation does not confer public listing approval. Follow the [complete public launch procedure](CHATGPT_LAUNCH.md) for account eligibility, packaging, publisher pages, review and publication.
