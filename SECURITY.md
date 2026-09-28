# Security Policy

OSCAR can eventually control computers, accounts, sensors and physical hardware. Security issues should therefore be treated as product-critical.

The detailed security and permission architecture lives in [`docs/SECURITY.md`](docs/SECURITY.md).

## Reporting a vulnerability

Do not open a public issue for vulnerabilities involving:

- authentication or authorization bypass;
- remote execution/control;
- Latch/device impersonation;
- leaked secrets or credentials;
- Voice Match bypass with consequential access;
- Sentry privacy exposure;
- unsafe physical-device behavior;
- memory or personal-data disclosure.

Prefer GitHub private vulnerability reporting when enabled for this repository. Otherwise contact the repository maintainer privately through GitHub before disclosing details publicly.

Include, where possible:

- affected component/slice;
- reproduction steps;
- expected vs actual behavior;
- impact;
- logs or traces with secrets removed;
- suggested mitigation if known.

## Security invariants

- Hardware emergency behavior must remain local and deterministic.
- Voice Match alone is not sufficient for critical actions.
- Generated skills/protocols cannot expand their own permissions.
- Embedded nodes should prefer outbound authenticated connections rather than public inbound endpoints.
- Secrets, personal memory, voice embeddings and raw private recordings must not be committed to the repository.
