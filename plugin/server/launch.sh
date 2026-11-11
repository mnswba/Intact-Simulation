#!/bin/sh
# Portable plugin command stays inside PLUGIN_ROOT; the installer prepares this runtime.
set -eu
intact_runtime_dir="${INTACT_RUNTIME_ROOT:-${HOME}/.local/share/intact-simulation/runtime}"
if [ ! -x "$intact_runtime_dir/.venv/bin/python" ]; then
  printf '%s\n' 'Intact runtime is missing. Run install-chatgpt-plugin.py on this computer first.' >&2
  exit 1
fi
exec "$intact_runtime_dir/.venv/bin/python" -m intact_backend.mcp_server
