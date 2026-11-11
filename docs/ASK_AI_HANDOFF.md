# Ask AI conversation handoff — 0.12.1

The screenshot exposed a single-turn task asking a clarification without providing a reply field. Ask AI now prefers ChatGPT's Browser Annotation API when the viewer is open in its built-in browser. A trusted button click calls `document.oai.annotation.request` synchronously, with the full description visible in the annotation target and a saved model/request identity in metadata. The native suggested comment is limited to 240 UTF-16 code units; the complete description (up to 4,000 characters), selected geometry, reference images and annotated viewport remain in `read_edit_request`.

Annotation acceptance means the host validated/queued the request. It does not prove that the editor opened or a message was delivered. The user reviews and sends the annotation, then continues in the current ChatGPT conversation. Refusals and exceptions produce a retryable explanation and never silently switch to isolated inference. An ordinary browser without this API retains the signed-in local task fallback, identified in the panel help.

All existing answered requests have a Reply field and per-request Reply buttons. Replies are child requests with ordered user/assistant history. Unchanged geometry retains its selected references and attachments; changed geometry retains conversation text but drops old numeric references. The scoped local worker receives that history too. Historical previews remain read-only. `respond_to_edit_request` lets ChatGPT publish clarification/completion text to the viewer without creating a CAD revision; `needs_reply=true` records an awaiting-reply state. Existing structured and Python CAD tools remain available.

Installed locally for Windows and Linux plugin profiles and the persistent viewer, preserving its address and user projects. Version 0.12.1 exposes 54 tools. Restart ChatGPT once to reload the changed tool catalogue and skill, then refresh the viewer.

Validation:

- 25 distinct backend tests across `test_chat_handoff`, `test_ask_ai`, `test_geometry_workflow` and `test_mcp` passed (overlapping runs: 22, 9 and 6).
- Seven Chromium browser groups passed against source; eight passed against the final installed runtime: trusted-click native handoff with selected geometry; reopening without duplicate requests; clarification replies; refused requests; host exceptions; long descriptions; ordinary-browser fallback; historical read-only controls.
- Fresh installed MCP client verified version 0.12.1 and the response tool; updated bundled skill validation passed.
- Disposable camera fixtures were used. The user's iPhone geometry was not edited.
- Native API behavior was simulated in Chromium. The actual Windows ChatGPT annotation editor and sending were not automated or verified. No connected document session was available. Evidence: `outputs/chat-handoff-audit/installed-browser.json` and `installed-reply-panel.png`.

Official API contract: https://learn.chatgpt.com/docs/annotations-extensibility
