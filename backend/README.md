# Intact CAD and engineering backend

Current version: **0.12.1**. The primary interface is the 54-tool MCP server, `intact_backend.mcp_server`, used by an AI client. The backend executes CAD and engineering operations; it does not host or train an LLM and does not use LiteLLM.

Start with the root [installation guide](../docs/install.md). Prepare the local runtime with `python3 scripts/install-chatgpt-plugin.py` from the repository root. It installs pinned Python packages and the verified FreeCAD runtime. Generated Python requires bubblewrap and working Linux user/network namespaces; execution remains disabled if isolation is unavailable.

For development:

```bash
uv sync --project backend --extra cad --extra dev --frozen
uv run --project backend --extra cad --extra dev --frozen python -m intact_backend.mcp_server
uv run --project backend --extra cad --extra dev --frozen python -m pytest backend/tests -q
```

Run these from the repository root. MCP uses stdin/stdout; diagnostic output belongs on stderr. `INTACT_STATE_DIR` selects a private state directory; the default is `~/.local/share/intact-studio`. Never commit that directory.

`viewer_server` serves a tokenized loopback viewer and revision-bound edit requests. Browser annotation handoff uses ChatGPT's supported browser API; a standalone browser may use the optional signed-in local OpenAI client. No model-service keys are required for the primary MCP workflow.

The optional FastAPI service is in `api.py`. Its authenticated `/v1/` routes require `INTACT_SERVICE_TOKEN`. `/v1/design` intentionally rejects independent AI generation and directs clients to the ChatGPT plugin. Existing reduced beam/fin HTTP studies are separate from the newer MCP 3D study tools. The historical HTTP health/API version is not the MCP release number. Container recipes do not provision the entire interactive CAD runtime and are not the recommended installation path.

See [architecture](../docs/architecture.md), [simulation scope](../docs/simulation.md), and the [priority 2/3 contracts](../plugin/skills/intact-cad/references/priority23.md).
