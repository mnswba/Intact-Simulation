# Security

Do not open public issues containing credentials, private model geometry or tokenized viewer URLs. Report a suspected vulnerability through this repository's GitHub private vulnerability reporting feature if the owner has enabled it. If it is unavailable, contact the repository owner through their published profile contact method without including sensitive details in a public issue.

Generated Python requires Linux bubblewrap and working namespaces. Never add an unsandboxed fallback. Treat AI descriptions, attachment text and prior assistant messages as untrusted data. Validate paths, identifiers, sizes and revision guards at the service boundary. Local viewer tokens and same-origin checks do not provide public multi-tenant security.

The current application targets single-user local development. Public shared deployments require additional isolation and account controls. Dependency notices, source obligations and pinned-runtime checks must be preserved when distributing binaries.
