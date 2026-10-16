# Integrated visual craft review — 2026-10-16

**Subsequent owner decision — 2026-10-16:** UI/UX **APPROVED / PASS**, including
this integrated artwork, all 15 heroes, Preferences and motion. The pending-review
statements and test receipts below describe the earlier capture run. Current
theme/lifecycle verification is in [FINAL-CLOSURE.md](FINAL-CLOSURE.md); this
historical receipt and its failed attempts are preserved.

The owner accepted the anchored navigation and motion, then requested a coherent
OSCAR identity across the actual app. The owner then clarified that transparency
alone was insufficient: artwork must bleed through the page edges and behind
the app bar rather than remain an inline thumbnail. The supplied boards establish
material, character and composition; they are references, not screen templates.
This follow-up supersedes earlier layout screenshots while preserving their
historical test receipts. Owner visual approval remains pending.

## What changed

- Ten transparent papercut derivatives remove rectangular backdrops, clipped
  UI fragments and noncanonical Orb slivers. Art now shares the page canvas in
  light and dark themes. The original 21 references and ten original crops are
  byte-unchanged. Full edit prompts, source/output hashes and alpha ranges are in
  [the derivative manifest](../../../../mobile/illustration-cutouts.json).
- Artwork is composed on the full scrolling canvas, outside the text gutter and
  behind transparent app bars, with native organic paper contours and deliberate
  cropping at screen edges. Text and controls retain a readable gutter. Different
  placements serve the wide Home/Automations scenes, right-edge device/Worker
  scenes, quiet Awareness room, notebook Reading and presence-led Access/Create.
  Heading clearance grows with content, keeping long and enlarged text legible.
- Native rounded line glyphs, colored medallions, section rules, status badges,
  paper fields and softly raised actions replace uniform stock controls. Field
  editing, password masking, button roles, disabled actions and minimum touch
  areas remain native and accessible. Pale status tones use readable dark ink.
- Conversation has inline OSCAR identity and a compact pinned composer. Reading
  uses a notebook scene and native selectable rich content. Voice centers the
  canonical shared expression, actual microphone state and one start/stop action.
- Automations uses distinct paper identities; task Activity uses actual-state
  timeline markers. Devices uses a scene cropped through its outer page edge,
  real connection status and expandable actual Grid rows. No promotional slogan
  or sample connected devices are introduced.
- Preferences combines flat grouped navigation with purpose-specific controls:
  expression preview, permission medallions, mode panels, visual theme samples
  and compact availability rows. At enlarged text sizes, control rows stack and
  headings expand naturally below the artwork.

The first inline-art candidate was rejected during this follow-up; it is not the
final visual target. Native comparison caught dark text inherited through the
transparent Scaffold, blurry small crops enlarged as heroes, and excessive dark
surface highlights. Explicit theme ink, crisp scene derivatives and restrained
highlights correct those issues. A soft dark header shade protects app-bar labels
and system icons where bright paper artwork reaches behind them. A native test asserts edge overflow, extension
behind the toolbar, artwork scrolling and readable light ink on dark Awareness.

The approved full-width bottom navigation and its travelling marker remain
unchanged. Filter motion, reduced-motion behavior, page entrances and disclosure
springs are preserved. No new runtime dependency was needed.

## Native visual evidence

[Primary screen contact sheet](craft/primary-contact.jpg) ·
[Preferences contact sheet](craft/preferences-contact.jpg) ·
[Dark 1.8× text contact sheet](craft/large-dark-contact.jpg)

The following panels pair the original reference with a current phone capture
at equal display widths and preserved aspect ratios. Differences in content
reflect current capability and the owner's later density/navigation decisions.

| Experience | Current comparison |
|---|---|
| Home | [Home](craft/comparisons/01-oscar-home.jpg) |
| Conversation | [Conversation](craft/comparisons/02-continuous-conversation.jpg) |
| Reading | [Reading](craft/comparisons/03-expanded-reading.jpg) |
| Voice | [Voice](craft/comparisons/04-voice-interaction.jpg) |
| Automations | [Automations](craft/comparisons/05-automations-overview.jpg) |
| Worker | [Worker](craft/comparisons/06-worker-detail.jpg) |
| Create responsibility | [Create](craft/comparisons/07-create-automation.jpg) |
| Activity | [Activity](craft/comparisons/08-activity-feed.jpg) |
| Task | [Task](craft/comparisons/09-active-task.jpg) |
| Decision | [Decision](craft/comparisons/10-approval-decision.jpg) |
| Devices | [Devices](craft/comparisons/11-devices.jpg) |
| Awareness | [Awareness](craft/comparisons/12-sentry-awareness.jpg) |
| Today | [Today](craft/comparisons/13-today-chief-of-staff.jpg) |
| Access | [Access](craft/comparisons/14-access-modes.jpg) |
| Preferences | [Preferences](craft/comparisons/15-preferences.jpg) |

All 11 Preferences subpages, the connection dialog and secondary navigation are
also captured separately in `craft/`. Captures use the isolated review package
on Samsung SM-S721B/API36 with synthetic fixtures. They are actual native UI,
not owner audio/biometric acceptance or live provider inference.

## Verification and boundaries

The exact build, installed APK hashes, test outcomes and capture hashes are in
[craft-review.json](craft-review.json). Coverage includes all production routes,
native rich Markdown/JSON, real disposable Core/Grid HTTP flows, independent
privacy grants, expiry/denial, encrypted recovery, keyboard/insets, landscape,
theme persistence, dark enlarged text and approved navigation motion.

Final complete run: **33 PASS / 4 SKIPPED / 0 FAIL**, 147.949 seconds. Gradle
assembly and lint pass (zero errors / 11 warnings), 28 JVM tests pass and the
24 scoped Python checks pass. There are 58 native PNG captures and 15 current
reference/native comparison panels. The final normal app is installed without
a data reset; its installed APK hash matches the verified artifact.

An initial complete run reproduced the historical expiry-review reset: the
session epoch advanced while foreground/interactive and later reconnected. The
exact initiating cause remains unconfirmed. A subsequent expiry run passed.
Another run missed Send and Save sources taps during keyboard movement. Those
two tests now explicitly dismiss and settle the keyboard before tapping; their
validation and authority assertions are unchanged. The focused recheck passed.
The receipt retains both failed runs rather than counting them as passes.
An additional pre-final canvas run completed the expiry/denial readback but its
Activity was destroyed before the last capture; its cleanup also failed. That
attempt remains recorded separately, with its initiating cause unconfirmed.

CoreSession, transport, Keystore/signing, native confirmation, native voice,
notifications and the shared Expression source remain unchanged from integration.
The canonical Orb and motion data are checked against packaged bytes. Scheduling,
provider briefs, Sentry and Secure/Full Access activation remain unavailable.
The original 56-row inventory and backend limits remain disclosed in
[the original-prompt audit](PROMPT-AUDIT.md).

The emulator stays off at the owner's request. GitHub Actions is disabled, so
remote CI remains blocked. Owner visual review, audio, biometric and OEM
commissioning remain pending; Gate C remains PARTIAL. No merge or release.
