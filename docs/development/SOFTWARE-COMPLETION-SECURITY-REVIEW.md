# Software completion: scoped security review

Reviewed 2026-10-24 at local checkpoint `fbe12e3`. This is a source and acceptance
review of the boundaries below, not an exhaustive penetration test, a dependency
vulnerability certification, owner activation or production acceptance.

| Boundary | Reviewed enforcement and matching evidence | Remaining limit |
| --- | --- | --- |
| Owner and device authority | Core enrollment proofs, exact signed reviews, standing-delegation bindings, scope/policy/account/session drift and revocation checks; current 1,035-test regression and native recovery receipts | Synthetic owners; actual owner activation and real-provider consent not performed |
| Native Android effects | Keystore session, durable pre-effect claim, current Core check, local selected-app/OS grants and monotonic action gate; actual clipboard/media/text readbacks and signed screen capture | Generic click and screen semantics remain partially verified. Android screen consent can include other visible content; only actual single-app OS consent was exercised here |
| Uncertain outcomes | Native transport failure stops execution. Actual Core restart preserved the session and prior claims, required explicit Worker restart and accepted only a fresh task | No automatic effect retry. Generic failure still requires inspection; service restart is not proof that an uncertain earlier objective completed |
| Running child process | Remote authority checks scheduled once per second, fresh checks before new effects; cancellation and actual POSIX/Windows process cases passed | The scheduled check also has the existing bounded transport deadline. Remote revocation is not an instantaneous process-kill guarantee |
| OAuth and MCP resource grants | Exact issuer/resource/scopes, PKCE, bounded loopback callback, encrypted native credential vault, same-grant reauthorization and account-generation fencing; installed MCP SDK/synthetic resource tests passed | Real providers uncommissioned. Dynamic registration, incremental challenges, automatic resource refresh and remote revocation are unsupported rather than implied |
| Local MCP process | Explicit trusted-process classification, environment filtering, bounded protocol calls and lifecycle cleanup | Trusted stdio runs with host-user filesystem/process authority. No OS sandbox is claimed; untrusted local execution must remain unavailable |
| Browser | Typed bounded plans, explicit origins and network-boundary checks, isolated owned profiles, exclusive bounded artifacts and supervised process cleanup; actual Chromium conversation/form/readback passed | Multi-step workflows can partially mutate. Anonymous HTTP-anchor downloads do not imply authenticated/blob download support. No CAPTCHA bypass, raw CDP, cookie extraction or request interception is enabled by the bounded workflow |
| Memory and perception | Canonical archive ownership, source-qualified recall, independent perception/retention/action grants, revocation lock through canonical mutation and physical deletion of derived projections | Deleting application records is not secure disk erasure. Single synthetic frame retention was explicitly authorized; no personal screen or audio was collected |
| Repository hygiene | Required files/local links and value-silent credential scan passed after the native acceptance change | Pattern scanning is not proof of absence of every secret; ignored synthetic fixture logs remain local |

The native acceptance investigation corrected host synchronization and test
UiAutomation flags. Three unsuccessful recovery campaigns and one unsuccessful
fixture-pixel campaign remain hashed in the passing receipts. They do not prove
an historical TLS failure cause, and they are not counted as acceptance.

## Requested Stealth Browser MCP evaluation

The [upstream README and trust model](https://github.com/vibheksoni/stealth-browser-mcp#trust-model)
were inspected on 2026-10-24. They describe trusted-client CDP/JavaScript,
cookie/storage and network-hook access. OSCAR's existing Playwright path already
implements the bounded ordinary-browser operations being accepted. Adopting
this server would add a broader trust surface without demonstrated isolation or
acceptance benefit for these workflows, so it was not installed or made a
runtime dependency. This is an architectural assessment, not a source-code audit
or a claim that the upstream server is vulnerable.

## Evidence

Selected Windows visual execution additionally separates `desktop:capture` from
`screen:retain` and existing control/file grants. Old invitations gain no screen
scope. The new frame path checks registered executable/process/window identity,
rejects overwrite/reparse destinations, caps pixels/PNG/pipe output and uses the
existing kill-on-close Job. Native input rechecks frame, foreground, point
obstruction and held input; its generic outcome remains partial. Fixture PNG RGB
and alpha were independently decoded, so a transparent or blank renderer report
does not establish acceptance. The actual signed synthetic Core/Worker campaign
retains native OS input and two independent exact owner reviews.

[Microsoft PrintWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-printwindow)
renders through the selected application and can block, which is why it stays
inside the bounded child. [SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
retains OS integrity restrictions. Frame equality and point checks cannot make
rendering/input atomic or establish a semantic objective. No image-model inference,
protected-desktop bypass or owner-application acceptance is claimed.

- [Integrated Python regression](../evidence/software-completion/regression-integrated-2026-10-24.json).
- [Constrained Linux runtime](../evidence/software-completion/linux-browser-fix-2026-10-24.json).
- [Browser process supervision](../evidence/software-completion/browser-supervision-2026-10-24.json).
- [Native Android Core recovery](../evidence/software-completion/android-recovery-2026-10-24.json).
- [Signed Android screen capture](../evidence/software-completion/android-screen-grid-2026-10-24.json).
- [MCP resource authorization](../evidence/software-completion/mcp-authorization-2026-10-23.json).

Later runtime changes need their own affected verification. This report does not
promote the full product to `SOFTWARE_FEATURE_COMPLETE`.
