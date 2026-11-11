# Privacy and data flow

CAD projects, revisions, artifacts and edit requests are stored locally in the selected `INTACT_STATE_DIR` (default `~/.local/share/intact-studio`). Runtime packages live separately under `~/.local/share/intact-simulation`. These directories are not included in this source repository.

The ChatGPT annotation flow attaches the description, selected geometry identity and chosen references to a user-reviewed annotation. Only the user sends it. The AI client can read geometry facts, CAD source and attached images through Intact tools to fulfill the requested task. Its provider's account/privacy terms apply to context sent to that client.

In a browser without the native annotation API, the optional Ask AI fallback starts a scoped task through the locally signed-in OpenAI client. It receives the chosen request and model context, uses restricted tools, and returns an answer to the viewer. It does not post into the existing ChatGPT conversation. No API key is copied into generated CAD workers.

The source repository contains authored examples and regression fixtures, not users' private CAD projects or model training weights. Intact's local CAD viewer does not add anonymous analytics. Separately deployed website/client hosting may have its own authentication and operational logging; review that configuration before deployment.
