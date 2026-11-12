# Privacy and data flow

CAD projects, revisions, artifacts and edit requests are stored locally in the selected `INTACT_STATE_DIR` (default `~/.local/share/intact-studio`). Runtime packages live separately under `~/.local/share/intact-simulation`. These directories are not included in this source repository.

Clicking Ask AI sends the description, selected geometry identity and chosen references to the AI workflow. If the supported ChatGPT component bridge is available, a follow-up message refers to the persisted model/request. Otherwise the viewer automatically starts a scoped task through the locally signed-in OpenAI client. The separate local task does not post into the open ChatGPT conversation. The AI client can read geometry facts, CAD source and attached images for the chosen request through Intact tools. Its provider's account/privacy terms apply to context sent to that client. No API key is copied into CAD workers.

Projects and request history remain in the chosen local state directory until the user removes them. The source package does not implement a hosted account deletion service. A future hosted edition needs its own declared retention/deletion controls and support contact. Do not describe the local workflow as fully offline: reasoning uses the user's signed-in OpenAI service.

The source repository contains authored examples and regression fixtures, not users' private CAD projects or model training weights. Intact's local CAD viewer does not add anonymous analytics. Separately deployed website/client hosting may have its own authentication and operational logging; review that configuration before deployment.
