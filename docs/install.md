# Installation and client support

## Supported host

Version 0.20.0 supports a native Windows x86-64 runtime. Linux x86-64 remains available through the source installer below. Native macOS is not implemented or validated. Ordinary web/mobile ChatGPT sessions cannot run this local Windows runtime.

## Native Windows 0.20.0

**For a new computer:** [download the Windows-Local ZIP](https://github.com/mnswba/Intact-Simulation/releases/download/v0.20.0/Intact-Simulation-0.20.0-Windows-Local.zip) and follow [Install Intact privately in Codex](INSTALL_WINDOWS_PRIVATE.md). That guide includes the exact installation request, version/readiness checks, checksum and design-transfer instructions. Do not use the automatic GitHub Source code archive as the plugin package.

### Use an existing local plugin installation

1. Enable Intact Simulation in the desktop host that installed the local plugin. This is separate from uploading a public-directory draft.
2. On first start, allow the launcher to prepare its pinned Python/CAD dependencies, FreeCAD, browser and local AI client when needed. Setup needs internet access, several GB of disk space and time to complete.
3. Ask Intact to check `status`. Confirm `version: 0.20.0`, `cad_ready: true` and `desktop_setup.ready: true` before modeling. Report setup errors instead of bypassing worker isolation.
4. Create a small dimensional example, check its measurements and export STEP. Open the returned viewer and check the version in **Tutorial**.
5. Use a new local conversation after an update when the old thread keeps its previous tool connection. An old WSL viewer URL can still point to 0.19.0; open the native Windows viewer rather than that stale link.

The small **Windows-Local** package contains the Intact wheel and uv launcher; larger runtime components are installed automatically in the user's profile. It requires no WSL or publisher-hosted CAD backend. Public-directory publication is pending and local-MCP submission access is a separate OpenAI requirement. See [release notes](RELEASE_0_20.md) and [submission status](CHATGPT_SUBMISSION_0_20.md). Do not treat this source repository as a live directory installation link.

Projects are stored separately in `%LOCALAPPDATA%/IntactSimulation/projects`. A local build suffix such as `0.20.0+local.1` selects a fresh plugin cache; the CAD runtime still reports 0.20.0. Preserve project libraries during reinstall/update. The installed desktop shortcut can open saved CAD without a geometry rebuild.

### Develop the Windows source runtime

Install Python/uv prerequisites using the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/), then run from PowerShell:

```powershell
git clone https://github.com/mnswba/Intact-Simulation.git
cd Intact-Simulation
uv sync --project backend --python 3.12 --extra cad --extra dev --frozen
```

For an MCP client that supports custom local stdio configuration, use the actual checkout path:

```json
{
  "mcpServers": {
    "intact": {
      "command": "uv",
      "args": [
        "run", "--project", "C:/path/to/Intact-Simulation/backend",
        "--python", "3.12", "--extra", "cad", "--frozen",
        "intact-simulation"
      ],
      "startup_timeout_sec": 300
    }
  }
}
```

The `intact-simulation` entry point runs desktop setup and then serves MCP over stdio. It is not a standalone chat UI: launching it in a terminal waits for an MCP client. Hosts differ in how they register custom tools and plugin skills; use their supported local installation/configuration mechanism. Do not substitute this JSON into a remote HTTPS connector field. The modeling skill and its references are in [`plugin/skills/intact-cad/`](../plugin/skills/intact-cad/).

The packaging source is `scripts/package-windows-local-loader.py`, using the backend wheel, uv installation and `backend/requirements-windows.txt`. The repository's native local installer helper is for the existing verified development-engine setup; it is not a universal fresh-machine GUI installer. The [verification record](QA_0_20.md) distinguishes tested startup from untested clean-account installation and records the Windows SDK viewer-disconnect limitation.

## Linux source installation and legacy WSL route

The Linux installer requires Python 3.12–3.13, uv, working namespaces and bubblewrap. Its pinned FreeCAD AppImage and library preparation target Linux x86-64. WSL2 Ubuntu is the legacy Linux-backed Windows route, not a prerequisite for the native Windows edition above.

The installer downloads approximately 0.8 GB of FreeCAD data plus Python wheels. Allow several GB of disk space. Install uv using its official instructions: https://docs.astral.sh/uv/getting-started/installation/ . On Ubuntu install `build-essential bubblewrap libgl1 libglu1-mesa libxft2` using apt. Additional browser libraries may be required for snapshots; Playwright reports missing dependencies for your distribution.

```bash
git clone https://github.com/mnswba/Intact-Simulation.git
cd Intact-Simulation
python3 scripts/install-chatgpt-plugin.py
```

The installer copies source into `~/.local/share/intact-simulation/runtime`, installs pinned CAD dependencies, verifies FreeCAD, prepares native libraries and registers the local personal ChatGPT plugin. User CAD projects remain in `~/.local/share/intact-studio`. These directories are separate from the repository.

For Windows ChatGPT run inside WSL:

```bash
python3 scripts/install-chatgpt-plugin.py --windows-home /mnt/c/Users/YOUR_WINDOWS_USER
```

The default WSL distribution is `Ubuntu-22.04`; pass `--distro YOUR_DISTRO` if needed. Restart ChatGPT to reload the plugin and select Intact Simulation. This is a local personal installation, not a public directory listing.

## Check the runtime

```bash
~/.local/share/intact-simulation/runtime/.venv/bin/python -c 'from intact_backend.program import ProgramService; from pathlib import Path; print(ProgramService(Path.home()/".local/share/intact-studio/programs").available())'
```

If this prints `False`, repair bubblewrap/user-namespace support before generating Python CAD. Do not bypass isolation. Check the MCP `status` tool from your client for CAD readiness and version. `status` does not replace an actual build/export test.

## Other MCP clients

After the runtime installer, use this stdio command on Linux or inside WSL:

```text
~/.local/share/intact-simulation/runtime/.venv/bin/python -m intact_backend.mcp_server
```

In a client's JSON configuration, replace `~` with the actual absolute home path; JSON command fields generally do not expand it. Windows desktop clients should invoke that command through `wsl.exe --distribution YOUR_DISTRO --user YOUR_LINUX_USER --exec ...`.

The repository includes `.claude-plugin/plugin.json` for local Claude Code development. From a prepared Linux/WSL clone, run `claude --plugin-dir .` to load its Intact tools and skill. The manifest uses `${CLAUDE_PLUGIN_ROOT}` for its launcher. It has been checked against the documented manifest layout, but live Claude Code operation has not been tested here. This does not create an Anthropic marketplace listing. Ask AI uses a direct ChatGPT component message bridge when supplied by the host; otherwise it starts a separate signed-in local task. MCP CAD operations are independent of that UI transport.

## Updates

Pull source updates and rerun the installer, then restart the AI client and refresh the viewer. Do not delete project state. This repository has no unattended updater or automatic remote publishing task.

## Optional website

The root `app/`, `components/` and `lib/` directories contain the website source. Use Node >=22.13, `npm ci` and `npm run dev` for development. Its hosting/authentication integration is separate from the local plugin. Configure only the optional backend values described in `.env.example`; do not put service credentials in client-side code. Public multi-user deployment requires additional authentication, storage partitioning, quotas and execution isolation work.

## Project files and DWG

The Project menu exports viewport PNG, a multi-view PowerPoint deck, a CSV BOM, and three-view 2D DXF/DWG drawings. `python-pptx` and `ezdxf` are included in the locked CAD extras. DWG uses the separately built GNU LibreDWG 0.14 `dwgwrite`/`dwgread` tools; the installer downloads SHA256-pinned source, compiles locally using gcc/make, retains its GPL license and validates DWG read-back. Build logs stay under `~/.local/share/intact-simulation/libredwg-build/build.log`. To repair only these tools, run the installed runtime Python on `scripts/install-project-tools.py`.

DWG output is R2000 with front/top/right wireframe projections in millimeters. Curved edges are polylines sampled from native topology, with no hidden-line removal, manufacturing dimensions or 3D solids. DXF/DWG require native CAD edges; mesh-only TPMS uses mesh/STEP conversion workflows instead. File compatibility with a particular third-party CAD application needs testing there. BOM rows represent saved named instances with quantity 1 and assigned model materials; the BOM includes hidden display parts and is not a supplier catalog. PPTX includes actual viewport captures and saved geometry measurements.

## Interchange formats and tutorial

Files & exports offers ASCII STL and Binary STL as distinct encodings, plus binary USD and readable USDA using locked OpenUSD (`usd-core`) bindings. These scenes preserve named part meshes, assembly placement, display colors, CAD Z-up and `metersPerUnit=0.001`; they do not carry native B-rep feature history. The existing AI export tool accepts `stl_ascii`, `stl_binary`, `usd` and `usda`. The viewer Tutorial button beside Settings provides a guided or searchable tour of 107 topics. Turning the tour off restores the original panel layout while leaving help readable.
