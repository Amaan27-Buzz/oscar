# Group 2.5A verification and independent review

## Final candidate â€” 2026-10-13

All Workspace routes have actual native captures in both themes. Native geometry
checks prove common heading/header left axes and no horizontal overflow at a
narrow Windows window. The fixed composer, compact typography, sidebar Orb and
icon-only Send are implemented; the original Companion remains unchanged.

Final independent visual review found no material layout blocker. It identified
a dangling executor separator and mislabeled narrow light evidence; both were
corrected. Final independent native review found no actionable authority or
preference-storage issue. Owner visual acceptance is PENDING.

Native preferences contain only theme, shortcut and enabled state, with bounded
parsing/validation and temporary-file replacement. Explicit debug review runs
skip owner preferences; authenticated reference sessions never write them.
Ordinary and non-reference enrolled runs preserve choices across restart.
No capture choice, context, task, policy, token or key is written to this file.

The older checkpoint narrative below is retained as iteration history. Its
runtime-local preference and pending-page descriptions are superseded by this
final candidate record.

**Historical checkpoint (superseded):** [implemented native Conversation, light and dark](conversation-review/README.md)
replaces Image Gen sketches as the current owner-review surface. Theme controls,
bottom sidebar expression and icon-only Send are real code. Remaining page,
full lifecycle and final candidate/PR acceptance are still pending.

**Historical design boundary (superseded):** owner feedback superseded the initial visual-review
disposition and requested simpler professional components, followed by individual
Image Gen screens with the canonical paper palette and matching dark mode.
[Screen feedback](../../../../desktop/design/workspace-screens/README.md)
is pending. The software/native evidence below remains valid at its recorded
scope; it is not acceptance of a final Workspace design.

## Functional checks

- Desktop TypeScript/build and React: 62 tests passed.
- Rust/Tauri: 14 tests passed; Clippy with warnings denied and rustfmt passed.
- Core regression: 559 tests passed, six existing skips.
- Shared Expression TypeScript build and 36 Expression Lab regression tests passed.
- Actual bundled Tauri/WebView2: full final checks in `evidence/acceptance.json`;
  existing native lifecycle CI check passed after updating its window-title selector.
- Native CNG-PSS, exact reviews, signed execution, UIA independent readback,
  cancellation, reconnect and shared-Core restart: `evidence/native-core.json`.
- Canonical Orb Git blob equals main: `cb38546cf40c585e1ea5a1f3000832ca10c92ba5`.

The native packet uses authenticated disposable Core tasks. Model transformation
and long answer fixtures remain SIMULATED / REPORTED. No owner audio is used.

## Independent code review

A GPT-6.1 Sol / Medium reviewer found three actionable issues: generic Tauri Any
event listeners could cross window privacy boundaries; Activity discard did not
clear local drafts; capture choice reset visually while native capture remained
configured. All were corrected and independently marked resolved. The reviewer
reran eight Workspace/TextTools tests. The final native run also caught a delayed-open navigation race; a regression now preserves the owner-selected page while newly received approvals still focus review. Real native checks also reject Companion
Desktop commands and event listening and prove capture-choice continuity.

## Independent visual review

A fresh GPT-6.1 Sol / Medium reviewer inspected the actual native capture matrix.
It matched the distinct Companion/Workspace responsibilities, typography,
materials, reading and exact approval hierarchy. It requested removal of heading
preambles, thick approval/dictation stripes and the duplicate activity badge.
Those were removed, the same views recaptured, and the reviewer scored all three
fixes resolved, with no visible regression from that batch: disposition `ship`
for the scored fixes. This is readiness for owner review, not owner approval.

## Historical limits (preference storage superseded above)

Tray menu handlers are native; direct tray-menu pointer acceptance remains an
owner check. Automated capture tests exercise global hotkey invocation, native
close/hide/reopen, Companion hide/show and explicit Quit/shortcut release.
Broad multimonitor interaction and physical voice/OEM/device acceptance are not
claimed. Preferences are runtime-local, as in the existing native contract;
restarting re-registers the default shortcut. Uncommissioned launch stays
unavailable. Installer/distribution and production enrollment remain separate.

No Mobile builds, Slice 14, merge or branch cleanup were performed.

## Preferences owner-feedback revision — 2026-10-13

[Preferences revision](preferences-review/README.md) supersedes the original
Preferences captures with visual theme choices, native-state shortcut switch and
purposeful reduced-motion-aware transitions. Frontend regression: 63 passed;
TypeScript/Vite and native Tauri debug build passed. Other route designs remain
at the earlier candidate. Owner visual acceptance remains pending.

## Devices, Preferences and app-wide spacing/motion — 2026-10-13

[Native revision packet](rhythm-review/README.md) records the Devices catalog,
finished lower Preferences sections, balanced header edges and shared content
rhythm across all six pages. Sliding navigation selection and bounded route,
capability and control feedback respect reduced motion. The first narrow-window
pass caught Companion action-row overflow; its width and inset were corrected.
Frontend regression: 64 passed. Native receipt and owner review remain distinct.

## Tactile material correction — 2026-10-13

The owner rejected the list-style Devices design and explicitly selected
neumorphism with more color and redesigned buttons. The current
[tactile revision](tactile-review/README.md) supersedes that iteration: executor
selection, a capability inspector, paired soft depth, Orb blue accents,
recessed inputs, pressed selection states and shared bounded motion. All 64
frontend tests and 53 native checks passed on the current bundled executable.
Owner visual acceptance remains pending.

## Forms and Activity correction — 2026-10-13

The owner rejected the heavy inset-button effect and raw composer affordance.
[Current native packet](forms-activity-review/README.md) records a bounded,
content-sized composer, one raised control treatment, grouped Act forms and a
focused Activity result/decision pane. Product banners/internal labels are
removed; exact review content, availability and outcome truth remain. Frontend
regression: 66 tests. Native acceptance: 56 checks. Final visual review remains
with the owner; this supersedes the preceding tactile controls.

## Act editor replacement — 2026-10-13

The owner rejected the stacked Act form. The current [action editor packet](action-editor-review/README.md)
replaces it with a destination/content editor and compact context/permission
support rail. Single-choice selectors are removed; real multiple choices and
capability-withdrawal recovery remain. Frontend regression: 68 tests; native
acceptance: 56 checks. Owner visual acceptance remains pending.

## Real library controls and refreshed light mode — 2026-10-13

[The latest native packet](library-controls-review/README.md) replaces native
browser arrows/triangles with installed Radix components and consistent plus/minus
markers. Non-modal choice popovers satisfy unchanged native CSP; native keyboard
selection, Escape focus return and disclosures pass in both themes. Light mode
uses the owner's new warm-chalk/white/slate-blue direction. Frontend: 70 tests;
native architecture/layout: 56 checks; additional library/CSP checks pass.
Owner visual acceptance remains pending.
