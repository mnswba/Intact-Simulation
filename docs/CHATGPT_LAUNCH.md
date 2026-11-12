# Publishing Intact Simulation to ChatGPT

Checked against OpenAI documentation on 12 November 2026. Product: **Intact Simulation**, plugin ID `intact-simulation`, release **0.19.0**. Publisher account/repository: `mnswba`. The public directory displays the developer identity verified in the submission account, not an identity established by this source code.

**The local development installation is not a public listing.** This release fixes the Ask AI submission flow and structural-analysis workflow. Public approval, publisher verification and a distributable clean-machine runtime remain separate launch work. Do not upload your private project directory, installed client profile or credentials.

## Can an individual engineer publish?

Yes. OpenAI supports individual identity verification and publication under your verified personal name; a registered company is not required for that route. Product name and publisher identity are different: the product may be Intact Simulation while its publisher is your verified name. GitHub ownership is not identity verification, account eligibility or directory approval. [Individual verification](https://developers.openai.com/plugins/deploy/submission).

The current local MCP edition also needs OpenAI partner approval and organization allowlisting. We have not established that this account has either. You may share the source and installation instructions on GitHub independently; directory listing remains a separate review. A hosted HTTPS edition is another development/deployment option, with identity verification, authentication, hosting and review requirements of its own. No hosted edition has been deployed by this repository update. [Local submission eligibility](https://developers.openai.com/plugins/deploy/desktop-only).

## Choose the correct route

Intact currently executes a local stdio MCP server, CAD workers and numerical solvers on Linux/WSL. The appropriate route is **desktop-only**. OpenAI currently limits local MCP submissions to approved partners: obtain organization allowlisting from an OpenAI representative first. These plugins run locally on desktop, rather than on ChatGPT web/mobile. Include the local server and its dependencies in the distributable package. [Official desktop-only instructions](https://developers.openai.com/plugins/deploy/desktop-only).

A future web/mobile edition needs a separately deployed public HTTPS MCP service, authentication, per-user project isolation and hosted compute. Our current localhost viewer is not that service. Publishing the GitHub repository or opening a localhost port does not implement it. Remote MCP submissions use the With MCP route and their own server review. [Remote server review](https://developers.openai.com/plugins/deploy/app-review).

## Prepare this product before submission

1. **Website and publisher:** replace any placeholder/domain-sale branding on `intactsimulation.com` with the actual product. Our inspection found domain-sale wording in the site's logo metadata. Confirm the intended publisher and a working support contact.
2. **Public pages:** publish support, privacy and terms pages under that publisher. The repository's [data-flow document](privacy.md) describes the implementation; it is not a substitute for approved business terms. The current plugin manifest intentionally does not invent missing policy URLs.
3. **Runtime distribution:** the `plugin/` folder is a development connector. Its launcher currently expects the runtime prepared by `scripts/install-chatgpt-plugin.py`. A source ZIP alone is not a standalone public plugin. Package the server plus the supported OS runtime/dependencies, license notices and setup instructions; test on a clean machine with no developer checkout. Do not include your personal `.codex` directory or model records.
4. **Viewer messaging:** Ask AI feature-detects the supported ChatGPT component message API. When absent in the top-level localhost viewer, it starts a separate scoped task through the signed-in local client. This does not insert a message into the open ChatGPT conversation. Test the exact ChatGPT desktop build used by reviewers and disclose this fallback. Delivering everything into the existing chat requires a host-supported component integration; annotation cannot silently submit on the user's behalf. [ChatGPT component bridge](https://developers.openai.com/plugins/reference).
5. **Scope:** advertise native CAD, supported TPMS meshes, kinematic previews, steady conduction, small-strain single-solid elasticity and bounded Stokes flow accurately. Do not advertise general vehicle assembly contact, nonlinear dynamics, turbulent CFD or autonomous walking as implemented physics.

The existing development installation can be checked with:

```bash
python3 scripts/install-chatgpt-plugin.py --windows-home /mnt/c/Users/YOUR_WINDOWS_USER
python3 scripts/check-publication.py
```

The first command runs inside WSL and installs the private development connector. The second runs from a clean source checkout. Neither submits a plugin or grants public-directory access.

## Account and upload steps

1. Sign in to OpenAI Platform with the account that will own Intact. Select the intended organization/project. Complete individual or business verification. Use an organization owner account or one with Apps Management Write.
2. Find the organization ID in Platform organization settings. Give it to your OpenAI representative and request local MCP submission eligibility. Wait for explicit allowlisting confirmation. We have not requested this or contacted anyone for you.
3. Prepare the desktop distribution ZIP after the clean-machine check. At its root, include `plugin.json`, `mcp.json`, skills, logo assets and the local server/runtime. Keep launch paths portable, using `${PLUGIN_ROOT}` where appropriate. The current listing metadata includes the logo and a short description; complete the verified publisher and real support/privacy/terms URLs before submitting. Root `plugin.json` in this repository and `plugin/plugin.json` represent different packaging roots; do not mix their relative paths.
4. Open the [Plugins submission portal](https://platform.openai.com/plugins), choose **Create plugin → Skills only → Upload ZIP** for an **approved local MCP submission**. Include the local MCP configuration. This special local submission route does not remove MCP from Intact or bypass approval. [Desktop submission route](https://developers.openai.com/plugins/deploy/desktop-only).
5. Select the verified developer identity, upload the package, and correct all metadata/skill validation findings. The actual publisher, logo, product description and public URLs must agree. Submit for review only after the required checks pass; publish from the portal after approval. [Upload, checks and publication](https://developers.openai.com/plugins/deploy/submission).

Open the live portal through the link in the official upload guide above; its controls and eligibility can change. Do not use the former ChatGPT plugin manifest/legacy plugin-store instructions.

## Review material prepared in this repository

[Review cases](launch-review-cases.json) supply five positive and three negative scenarios with prompts, expected tools and expected results. They are a proposed reviewer script, not a claim of successful directory review. Record a short end-to-end desktop demonstration showing installation, creating a model, selecting geometry, an Ask AI edit, a clarification reply, a real structural result and exports. Keep test credentials in the secure submission form if requested, never in a ZIP. Remote MCP reviews require five positive and three negative cases, demo access and a demonstration video; use these cases for the desktop review as requested by your representative. [Review evidence requirements](https://developers.openai.com/plugins/deploy/app-review).

The included logo is an authored Intact cube/letter-I SVG. Confirm your preferred branding before publishing. The source license and dependency notices are in `LICENSE`, `THIRD_PARTY_NOTICES.md` and the priority-1/2/3 inventories.

## After approval

Publish, install the directory version in a fresh desktop profile, and repeat the reviewer script. Keep source changes and release notes on GitHub, increment the version consistently, preserve user projects during upgrades and submit updated package metadata/skills through the portal. Track support reports with model/revision IDs and solver evidence; never ask users to post confidential CAD or credentials in public issues.
