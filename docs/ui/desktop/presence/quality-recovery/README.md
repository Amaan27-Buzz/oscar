# Slice 12.1 corrective candidate — owner review

2026-10-11. Branch `fix/slice-12-1-presence-quality`, based on exact candidate
`5fea2071e891adf0fac7f9838ee556c9a60e1e1c`. Integration ancestor:
`b9d3e049aef5148a10c710626b9e6b06771c9229`. **DRAFT / OWNER APPROVAL REQUIRED.**
No merge, default-presence promotion or Slice 12.2 work.

Start with the [current native sheet](evidence/native-review-sheet.png),
[original failures versus correction](evidence/before-after-failures.png), then
the recordings below. Historical [6.7 review](../INDEPENDENT-REVIEW.md) and
[verdict](../OWNER-VERDICT.md) remain unchanged.

| Review question | Actual native evidence |
|---|---|
| Quiet, compact character | [idle](evidence/after-idle.png) |
| Draft and writing leaf after reinvocation | [reinvoked](evidence/after-reinvoke.png) |
| Missing capability versus denied permission | [blocked](evidence/after-blocked.png), [denied](evidence/after-denied.png) |
| Owner attention before opening | [compact approval](evidence/after-approval-compact.png) |
| What needs review and exact review route | [attention](evidence/after-approval.png), [corrected authoritative destination](evidence/corrected-review-route.png) |
| Executing versus awaiting result | [working](evidence/after-working.png), [waiting](evidence/after-waiting.png) |
| Verified and partially verified answers | [verified arithmetic](evidence/after-verified.png), [scripted reported answer](evidence/after-partial.png) |
| Failure survives reconnect | [failure](evidence/after-failure.png), [offline](evidence/after-offline.png), [restored](evidence/after-restored.png) |
| Native accessible rendering fixtures | [reduced motion](evidence/native-reduced-motion.png), [forced colors](evidence/native-forced-colors.png) |

## Motion at recorded cadence

- [Invocation, repeated interrupted retreat and reinvocation](evidence/native-invoke-retreat.gif).
- [Finite weighted work phrase and verified recovery](evidence/native-weighted-work.gif).
- [Authoritative completion interrupts the active phrase](evidence/native-interrupt-recovery.gif).
- [Original candidate sample](evidence/baseline-motion.gif); only ten frames, so
  it does not establish the original character's full cadence.

These are actual Tauri/WebView2 frames, captured through its debug CDP endpoint.
Transparent captures are aligned at the bottom right over a neutral canvas;
GIFs use measured frame intervals, with a final 500 ms hold and palette
quantization. They are **native WebView content recordings**, not whole-desktop
compositor videos. Original raw PNGs and capture timestamps remain in
[the final 13-check receipt](evidence/native-suite.json) and
[interruption receipt](evidence/native-interrupt-suite.json).
The fresh reviewer caught the review being below the initial viewport. The
opt-in focus/scroll correction was then verified separately with
[four native assertions](evidence/review-route-receipt.json); the earlier
[handoff capture](evidence/after-exact-review.png) is preserved as before evidence.
The labelled frame sheets select 24 frames from each final manifest; they are
annotations, not additional original captures.

## Reproduce locally

Use Node 24.21.0 and Rust 1.99.0, then from this corrective worktree:

```powershell
cd desktop
npm run dev
```

Keep the owned Vite server on localhost 1420. In another terminal at repository root:

```powershell
cargo +1.99.0 build --manifest-path desktop/src-tauri/Cargo.toml --locked --no-default-features
python -m scripts.desktop_presence_quality_acceptance
```

The runner uses the real native binary, an authenticated temporary Core,
real task readback and harmless reference executors. It requires the existing
Python browser/mobile development extras and Pillow for captures. No new product
dependency is added. Do not run two native fixtures concurrently: the global
shortcut belongs to one process. The runner overwrites **this corrective
package's** evidence; preserve a copy before another review run.

For manual developer exploration, `python -m scripts.desktop_presence_quality`
accepts the commands printed on startup. `execute`/`work` progress the disposable
Runtime programmatically: **this is not GUI owner approval acceptance**.
`reported`/`failure` use a scripted model, not real inference. Credentials exist
only in the temporary native bootstrap; React receives no tokens or signing keys.
The production entry point excludes the presence and synthetic previews.

## Boundaries and provenance

Read [changes](CHANGES.md), [root causes and regressions](ROOT-CAUSES.md), and
[validation](VALIDATION.md). The separate fresh-context review is in
`INDEPENDENT-REVIEW.md` and `OWNER-VERDICT.md` alongside this README when complete.
[Asset hashes and readable-image metadata](artifacts.json) and
[preserved historical review hashes](baseline-provenance.json) make the evidence
auditable. Screenshots contain disposable arithmetic/reference drafts and
application crops; no owner archives, credentials or private recordings were
included. Original historical screenshots were not altered.

At the owner's request, final verification used no computer use. Native CDP
checks establish WebView focus, IPC acknowledgements and real window content.
They do not establish OS focus stealing, human tray interaction, real approval
dialogs, desktop click-through, fullscreen compositing, multiple monitors or
100%/150% DPI acceptance. Those remain **NOT VERIFIED**. The recorded WebView
device scale was 1.25; that alone is not complete Windows 125% acceptance.
