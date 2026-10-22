# HTTP error response cleanup — 2026-10-22

The ongoing full Windows Python run exposed `ResourceWarning: Implicitly cleaning up
<HTTPError ...>` warnings. Owned urllib error responses now close explicitly in OAuth
request/revocation, GitHub device flow, reference action/control transport, model
generation and discovery. Search closes its response before capacity persistence,
including when that persistence fails. Provider error bodies close in `finally`,
including an incomplete read. Public source, connector, remote client and ambient
error cleanup already existed and were not changed by this patch.

Failure categories, status codes, provider retry metadata, redacted errors and
unverified action/control outcomes remain unchanged. No retry was added.

Validation used synthetic streams and loopback servers: 40 provider/resource tests
passed in 29.201 seconds; 84 OAuth/search/reference transport tests passed in
24.423 seconds. Ruff passed for the six changed production modules and two test
files; mypy passed for the six production modules. The new resource contracts
check stream closure, single attempts, preserved status/category/retry metadata,
and a storage failure during search error processing. The existing incomplete
provider response test now also checks that the response closes.

Receipt: [source and validation](../evidence/software-completion/http-resources-2026-10-22.json).
Logs are local ignored `.oscar/software-http-resource-focused.log` and
`.oscar/software-http-resource-contracts.log`. These checks do not establish that
the earlier full-suite run was warning-free, nor do they commission external
providers or accounts.
