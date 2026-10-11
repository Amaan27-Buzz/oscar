# Group 1 independent critical review

Reviewed 2026-10-11 in `build/slice-12-desktop-completion` against corrective base
`da8fddae50112c8859b21247d0cbaa617be8667e`. This reviewer made no implementation
changes. The candidate was changing during review; evidence and tests below are
local observations, not an immutable remote-head certificate.

**Final recommendation: ACCEPT bounded Group 1 software closure and use as the
next software-group baseline when that group's scope is separately authorized.**
The initial exact-review and bounded-output findings below are corrected and
independently rechecked. No demonstrated P0/P1/P2 release blocker remains in the
reviewed software paths. This is not owner approval or production acceptance.
Manual/device acceptance may remain deferred under the owner's software-first
strategy. These two findings concern software truth and authority, so that
deferral does not waive them.

## Evidence-first assessment

Before reading the completion implementation report, inspected native PNGs from
12.2–12.6, the character sequence, original 12.1 native invocation, and corrective
idle/approval/interrupt/recovery captures. Decoded multiple frames of the original
`native-invoke-retreat-reinvoke.gif`, corrective `native-weighted-work.gif`, and
completion `12-6-native-motion.gif`. Read the raw completion archive named in
the native receipt and independently checked **47 hashes, zero mismatches**.
Raw images preserve actual native viewport dimensions, 165×185 and 540×520;
they are not full-desktop compositor captures.

The completion GIF has 41 encoded frames, 120–540 ms encoded durations and 5.75 s
total duration at initial inspection. Repeated frames are coalesced; the receipt
reports 47 captured frames with median 127 ms and maximum 140 ms capture interval.
This supports a finite changing character phrase, readable state transitions and
spatial continuity. It cannot establish 60 FPS or smoothness between captures.
The wider puck-range metric covers the whole sequence, including hover/attention;
it must not be described as isolated working motion. Waits between recorded
segments are cut. No owner-naturalness verdict is inferred from this GIF.

The new surfaces extend the corrected writing leaf coherently. Compact presence
retains the blue shell, yellow weighted puck and canonical wink. Work changes
gaze/marks/pose without adding another mascot. Attention has an explicit amber
caption and clear decision path. Long answers and text/action forms progressively
expand; Activity now retains the same character and bounded leaf rather than
becoming a disconnected full-window dashboard. Original evidence and earlier
reviews remain historical, not overwritten acceptance.

## Release findings

### Initial P1 — Exact approval review silently omits part of a valid plan — RESOLVED

`oscar/desktop.py`, `Desktop.challenge`, serializes transient parameters and slices
the string to 12,000 characters. The new Activity sheet calls that string **Exact
reviewed material**, while native confirmation signs a digest of the complete
descriptor and Core executes complete parameters.

Independent disposable reproduction: an Edit instruction of 4,096 characters with
an admitted focused context of 8,192 characters produces a serialized review of
12,374 characters; the presented review is 12,000, hiding 374 characters without
an omission warning. Escaped JSON can also increase serialized size. The request
respects existing input bounds. A signature/digest protects against mutation; it
does not make unseen material reviewed.

Required correction: provide the full review within an explicit safe native bound
or fail closed before issuing a confirmable challenge. Do not silently omit
material and retain an exact-review claim. Add a boundary regression.

Final independent recheck: the actual bounded Edit reproduction now presents all
12,374 characters and parses to exactly the transient parameters. Core admits a
complete review up to 24,000 UTF-8 bytes; oversized multibyte material raises
specific shorten-request feedback **before** creating any challenge. Independently
observed zero additional challenges in that negative case. Native review admission
uses a compatible 24,000-byte bound (`str.len()`), while other review fields retain
12,000-byte limits and transport/signing-envelope bounds remain intact.

### Initial P2 — Worker excerpt can be presented without its truncation warning — RESOLVED

`Desktop.inspect` selects `worker_outputs[target][result.action_id][:8192]` as
the displayed response, but derives `response_truncated` from `result.value`.
Worker output and result summary are separate sources; real machine file,
PowerShell and Git paths use the output collection.

Independent disposable reproduction: successful result value `short` with a
9,000-character Worker output yields an 8,192-character response and
`response_truncated=False`. ResultView and Activity consequently omit the bounded
excerpt warning, making an incomplete output appear complete.

Required correction: derive truncation from the source actually selected for
display; cover long Worker output with a short result summary.

Final independent recheck: source selection records the actual chosen length;
the original short-value plus 9,000-character Worker output now returns 8,192
characters with `response_truncated=True`. The regression tests cover that path.
When recalled support is withdrawn and replaced by UNKNOWN text, the obsolete
truncation flag is cleared as well.

### Session review boundary — independently rechecked after tightening

Initial probing found a replacement owner session could review prior planned input
after explicit key enrollment, although ordinary private responses were withheld.
The implementation now consistently applies `private_for` to presentation, review
and approval completion. Explicit key enrollment does not inherit earlier RAM-only
private inputs. Independently paired and enrolled a replacement session: approve
was absent; denial remained available with review `{}` and no sentinel input.
Safe shared task metadata, denial and cancellation remain permission-scoped.

## Code and verification assessment

Read DESIGN.md, TASTE.md, Product, Expression Core, Desktop redesign, Security,
Engineering, and the relevant authority/epistemic contracts. Inspected changed
Core Desktop/voice/memory execution, native Bridge/protocol/window behavior and
React Ask/results/text/actions/Activity composition against the corrective base.

Independent checks:

- **43 Python tests passed**, Desktop and completion modules, no skips/failures.
  These exercise signed approval, policy recheck, replay/changed-plan rejection,
  revoked/foreign/stale context, expected-value fencing, Worker loss, restart,
  discard during execution, sourced recall/forget and voice cancellation.
- **38 frontend tests passed across six files**: Living, TextTools, Activity,
  ActionSurface, Act and ResultView. Expiry, unavailable controls, cross-mode
  active tasks, draft preservation, exact destinations and result evidence tested.
- **12 Rust tests passed**, none ignored: stale voice/content fencing, signing
  boundary, switched-review invalidation, discard and public-state sanitation.
- Independently reproduced both release findings above with disposable Core state.
  No owner content, private recordings or credentials used.

After the final corrections, independently reran **46 Python Desktop/completion
tests**, zero failures/skips, 16.955 s, and **12 Rust tests**, zero failures/ignored,
2.05 s. Repeated the actual long Edit, oversized multibyte, replacement-session
and Worker-output reproductions as separate disposable self-checks. Frontend
implementation was unchanged by these final Core/native-bound corrections; the
38-test frontend run above remains applicable.

Core continues to own permission, tasks, memory provenance and verification.
Native Rust owns admission, signing, ordering and window lifecycle. React supplies
presentation/drafts; no second authority, memory engine or executor was added.
Cancelled recognition is generation-fenced; discard withdraws private presentation
while active execution keeps independent verification. Missing recall/provider
capability remains blocked. REPORTED/RECALLED/INFERRED/UNKNOWN remain separate from
VERIFIED. Opening Activity or a review creates no consent.

Native receipt inspection supports real WebView2 rendering and disposable Core
task/state/readback. The CNG/UIA receipt reports actual native signing and registered
application readback, but scripted model/edit progression and unrun microphone are
explicit. This reviewer did not rerun a native fixture while the parent owned the
serial fixture slot. Parent regression claims are not counted as independent runs.

## Ten-category UX score

Scores describe the observed software candidate, not owner approval. The mean is
**7.8/10**; no release finding is excused by that average.

| Category | Score | Reason and limit |
|---|---:|---|
| Character identity | 8.5 | Blue shell, yellow puck and wink remain distinctive at compact scale; immutable source untouched in diff. |
| Expression | 7.7 | Finite gaze/mark changes and stronger attention state; tiny-scale nuances still depend partly on labels. |
| Motion | 7.2 | Weighted work and finite settle are visible across frames; capture cadence cannot prove compositor smoothness. |
| Responsiveness | 7.8 | Focus, preserved drafts, interruption/reversal and state acknowledgement tested; no independent OS foreground measurement. |
| Composition | 7.8 | One dominant task per leaf with deeper detail; text/action forms require substantial vertical scrolling. |
| Typography | 7.8 | Legible native system type and restrained hierarchy; technical IDs and approval metadata remain dense. |
| Compact presence | 8.2 | Small recognizable object, honest short captions and quiet idle; desktop-background/hit-region comfort deferred. |
| Expansion/retreat | 7.2 | Spatial origin and draft continuity survive captures/tests; Activity replacement has less choreography than the primary leaf. |
| Windows native feel | 7.4 | Actual Tauri/WebView, native window/signing and scoped UIA contracts; tray/OS focus, multi-monitor/DPI and human confirmation deferred. |
| Overall coherence | 8.0 | Shared character and progressive tools avoid dashboard gravity; candidate remains a debug review path rather than accepted distribution. |

## Acceptance boundary

With the software findings independently rechecked, this can serve as a **bounded
next software-group baseline**, subject to separate authorization to begin that group.
That recommendation is distinct from default-presence promotion, owner visual
approval, production readiness, remote CI, signed distribution or merge approval.
No physical GPIO/voice/phone, owner microphone, native human consent, DPI,
screen-reader or sustained daily-use PASS is granted. Gate C remains PARTIAL.

Not checked: owner use, physical/device/DPI/compositor acceptance, distribution,
real model inference or remote exact-head CI. Remaining risk: subjective movement
and native desktop comfort need the consolidated owner review.
