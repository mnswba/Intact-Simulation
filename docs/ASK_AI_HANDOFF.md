# Ask AI delivery · 0.16.0

Ask AI persists the full description, native geometry selection, source revision/artifact, references and optional viewport image before starting work. It never enters the native Annotation editor.

When the host exposes `window.openai.sendFollowUpMessage`, the viewer posts a follow-up carrying the saved model/request ID and description. ChatGPT reads `read_edit_request`, completes the request or asks for clarification, and publishes the answer with `respond_to_edit_request`. This host capability is feature-detected; the localhost browser does not automatically have it. [Supported bridge](https://developers.openai.com/plugins/reference).

Otherwise a click automatically starts the model-scoped task using the locally signed-in OpenAI client. This is a separate task whose progress, answer and replies appear in Intact. It does not join the current ChatGPT conversation. There is no LiteLLM or additional model-service API key. A bridge error is shown for retry, rather than silently launching a duplicate local task.

Replies retain conversation history and current references; stale numeric references are dropped after geometry changes. Historical previews remain read-only. Simulation requests cannot mutate CAD. Mechanical Ask AI runs actual analysis after material, supports and loading are sufficiently defined; preparation alone is not success. Clarification replies and failed/convergence-limited studies have explicit states.

The browser Annotation API requires the user to submit its editor. We therefore do not use it as an automatic Ask AI transport. [Annotation API behavior](https://learn.chatgpt.com/docs/annotations-extensibility).

See [launch requirements](CHATGPT_LAUNCH.md) for the distinction between the private installed connector, direct component messaging and public directory approval. Tests distinguish mocked host bridge contracts from live local-client/solver execution.
