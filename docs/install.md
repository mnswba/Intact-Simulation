# Installation and client support

## Supported host

Use Linux x86-64 or WSL2 Ubuntu on Windows. Python 3.12–3.13, uv, working Linux namespaces and bubblewrap are required. The pinned FreeCAD AppImage and engineering library preparation currently target Linux x86-64; other architectures and native macOS/Windows are not supported by this installer.

The installer downloads approximately 0.8 GB of FreeCAD data plus Python wheels. Allow several GB of disk space. Install uv using its official instructions: https://docs.astral.sh/uv/getting-started/installation/ . On Ubuntu install `bubblewrap libgl1 libglu1-mesa libxft2` using apt. Additional browser libraries may be required for snapshots; Playwright reports missing dependencies for your distribution.

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

The repository includes `.claude-plugin/plugin.json` for local Claude Code development. From a prepared Linux/WSL clone, run `claude --plugin-dir .` to load its Intact tools and skill. The manifest uses `${CLAUDE_PLUGIN_ROOT}` for its launcher. It has been checked against the documented manifest layout, but live Claude Code operation has not been tested here. This does not create an Anthropic marketplace listing. The Ask AI browser annotation bridge is specific to ChatGPT's built-in browser; MCP CAD operations are independent of that bridge.

## Updates

Pull source updates and rerun the installer, then restart the AI client and refresh the viewer. Do not delete project state. This repository has no unattended updater or automatic remote publishing task.

## Optional website

The root `app/`, `components/` and `lib/` directories contain the website source. Use Node >=22.13, `npm ci` and `npm run dev` for development. Its hosting/authentication integration is separate from the local plugin. Configure only the optional backend values described in `.env.example`; do not put service credentials in client-side code. Public multi-user deployment requires additional authentication, storage partitioning, quotas and execution isolation work.
