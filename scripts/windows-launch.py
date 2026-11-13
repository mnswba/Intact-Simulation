"""Launch the bundled MCP server; sitecustomize configures portable dependencies."""
import sys
if sys.platform!='win32':
    raise SystemExit('This Intact Simulation package supports Windows x86-64 desktop only.')
from intact_backend.mcp_server import main
main()
