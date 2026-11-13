# Install Intact Simulation on another Windows computer

**Version 0.20.0 · Windows x86-64 · private local installation**

You do not need public ChatGPT-directory approval to use this package privately in a supported local Codex/ChatGPT desktop host. A local marketplace is separate from the universal public directory. See [OpenAI's local-marketplace instructions](https://developers.openai.com/plugins/build/plugins#how-local-marketplaces-work).

## 1. Download the Windows plugin

[Download Intact-Simulation-0.20.0-Windows-Local.zip](https://github.com/mnswba/Intact-Simulation/releases/download/v0.20.0/Intact-Simulation-0.20.0-Windows-Local.zip)

Save the ZIP in the new computer's Downloads folder. Use the Windows-Local package, not GitHub's automatically generated Source code ZIP. The plugin archive is 15,755,028 bytes (about 15.8 MB).

SHA-256:

```text
3ea9a3c712aa501877fd9b6b1e3742f26fd337257f438af6972393efc69ddfca
```

Optional checksum verification in PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath "$HOME\Downloads\Intact-Simulation-0.20.0-Windows-Local.zip"
```

## 2. Install and sign in to Codex

Use a local Windows Codex host with access to your Downloads folder, and sign in using your own ChatGPT account with Codex access. [Official Codex setup](https://learn.chatgpt.com/docs/codex/cli).

The current package is for Windows x86-64. It does not run natively on MacBook/macOS or in an ordinary web/mobile chat. No WSL or publisher-hosted CAD server is required.

## 3. Ask Codex to install the private plugin

Open a local Codex conversation with access to the folder containing the ZIP. Paste this request, replacing the location if you saved the file elsewhere:

> Install Intact Simulation from `Downloads/Intact-Simulation-0.20.0-Windows-Local.zip` as a private local plugin on this Windows computer.
>
> Extract it into a permanent user-owned folder. Create or add a local marketplace entry without overwriting any existing plugins or marketplace entries, then register and install it using this Codex version's supported plugin commands. Use the plugin's bundled skill and its local stdio MCP configuration. Preserve the contained `./bin/uv.exe` command and `${PLUGIN_ROOT}` arguments.
>
> Do not use WSL, create a hosted CAD service or copy another person's credentials. Let automatic runtime setup finish. Verify the runtime version is 0.20.0, CAD is ready, desktop setup is complete and all 65 tools are available. Report setup errors accurately.

Codex should use its supported local-plugin workflow rather than the public submission portal. The Windows source installer helper in this repository is for the existing verified development-engine setup; running that helper is not a prerequisite for installing the standalone Windows-Local package.

## 4. Restart, enable and wait for setup

Restart the desktop host after installation and start a new local conversation with Intact enabled. Existing conversations may retain their previous connection.

First use automatically installs the pinned Python/CAD libraries, FreeCAD, browser-rendering components and the OpenAI local client when needed. Allow internet access, several GB of free disk space and time to finish. Future starts reuse the local cache. Ask Intact to check `status` and confirm:

```text
version: 0.20.0
cad_ready: true
desktop_setup.ready: true
65 tools available
```

If a standalone viewer's Ask AI needs sign-in, use your own account in the official local client. Do not share passwords, API keys or sign-in profiles.

## 5. Create and verify a first model

> Using Intact Simulation, create an 80 mm diameter flange, 8 mm thick, with a 24 mm bore and six 6 mm through holes on a 60 mm bolt circle. Verify the native dimensions and hole positions, export STEP and STL, and open the viewer.

Open **Tutorial** in the viewer and check that it displays **0.20.0**. Inspect the model and export evidence rather than accepting a screenshot alone. [Viewer tutorial](https://www.intactsimulation.com/how-to-use/).

## Move your designs separately

The plugin ZIP contains no private models or sign-in data. Export a design as **project JSON** on the original computer, transfer it and import it on the new one. Each computer runs its own CAD processing; the original laptop does not need to remain connected.

## Troubleshooting and scope

- **Plugin missing:** confirm the local marketplace points to the extracted plugin folder, install/enable it, restart and use a new local conversation.
- **Old viewer version:** open the new installation's returned viewer link instead of a previous WSL or saved browser link.
- **First setup failed:** read the reported error, confirm network/disk availability and retry. Do not disable CAD worker isolation.
- **Viewer closes after disconnect:** some Windows MCP SDK clients terminate child viewers on shutdown. Reconnect and ask Intact to open the saved model again. The separately launched desktop viewer avoids that client-owned process lifetime. Models remain saved locally.
- **MacBook:** native macOS is not supported by this Windows package.

This is a local edition, not a public ChatGPT-directory approval or a promise of clean-machine compatibility on every Windows configuration. [Measured tests and known issues](QA_0_20.md) · [Support](https://www.intactsimulation.com/contact/).
