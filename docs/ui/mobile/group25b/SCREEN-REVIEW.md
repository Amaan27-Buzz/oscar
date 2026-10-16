# Whole-app screen review — 2026-10-15

The later [integrated craft review](CRAFT-REVIEW.md) supersedes the screenshots
below with current native components, blended illustrations and full route
captures. The earlier density/navigation corrections remain part of the design.

The owner requested a comprehensive correction for text-heavy developer-facing
screens and duplicated navigation. This review covers all 15 hero experiences,
all nine additional settings pages and the connection dialog. The original
ImageGen/Figma artwork remains preserved; the owner's later direction supersedes
promotional compositions and unnecessary copy in the production app.

The [Preferences follow-up](PREFERENCES-REVIEW.md) supersedes the settings-page
compositions below. Its current screenshots cover the root and all 11 subpages
at normal size and dark 1.8× text. Older captures remain tied to their original
verification receipts.

The subsequent [motion review](MOTION-REVIEW.md) replaces the static navigation
selection with an anchored travelling marker and adds fluid filter/expansion
behavior. Its receipt supersedes earlier installed-APK hashes.

Primary Conversation, Automations and Activity retain one shared three-tab bar.
Secondary pages have one titled Back bar and no bottom tabs or duplicate body
Back buttons. Back returns to the invoking primary tab; Privacy reached from
Awareness returns through Awareness and Preferences. The same routing handles
Android Back. Reading, Task and Decision each have one full-screen detail bar.
At large Android text sizes, tab widths follow label length and use the available
screen width; labels retain the requested font scale. A native 1.8× check verifies
that all three labels stay on one line without clipping on the review phone.

Long status messages use a temporary, dismissible notice in allocated layout
space. An initial device run exposed a floating notice covering Voice and lower
settings rows; the corrected layout reserves space above the composer. Notices
remain scoped to the current privacy/source epoch. Full error text is retained.

| Screen | Review and correction | Current capture |
|---|---|---|
| Home | Pinned composer, contextual connection action, no unrelated private-discard footer | [Home](native/01-oscar-home.png) |
| Conversation | Removed duplicate active-task summary for tasks already in the conversation; shortened status labels | [Conversation](native/02-continuous-conversation.png) |
| Reading | Content-first layout, compact request heading, full native rich response; source/verification disclosure | [Reading](native/03-expanded-reading.png) |
| Voice | One start/stop action, one Back action; permission and enrollment details disclosed separately | [Voice](native/04-voice-interaction.png) |
| Automations | Short truthful availability, smaller artwork, functional responsibility entries | [Automations](native/05-automations-overview.png) |
| Worker | Removed promotional hero; honest assignment status and disabled Run; scope on demand | [Worker](native/06-worker-detail.png) |
| Create responsibility | Native draft fields first, scope/access disclosure, truthful scheduling limitation | [Create](native/07-create-automation.png) |
| Activity | Short empty/disconnected state; one task entry instead of repeated Inspect controls | [Activity](native/08-activity-feed.png) |
| Task | Smaller side artwork, current status/result first, evidence and metadata behind details | [Task](native/09-active-task.png) |
| Decision | Compact exact action, consequence and target; plan review, expiry and native confirmation preserved | [Decision](native/10-approval-decision.png) |
| Devices | Compact phone and actual Grid rows; capabilities/work/IDs expand; no promotional hero | [Devices](native/11-devices.png) |
| Awareness | Off status, compact mode/grant rows; no repeated Privacy entry or page navigation | [Awareness](native/12-sentry-awareness.png) |
| Today | Real device-local date, compact source availability and planning entry; no invented brief | [Today](native/13-today-chief-of-staff.png) |
| Access | Ask status and mode meanings; activation and delegation constraints remain explicit | [Access](native/14-access-modes.png) |
| Preferences | Removed promotional heading/artwork; one native settings list and connection disclosure | [Preferences](native/15-preferences.png) |
| Persona | One canonical Orb preview and selected expression chips; preview-only status retained | [Persona](screens/review-persona.png) |
| Voice settings | Real Android grants and output route; setup detail behind disclosure | [Voice settings](screens/review-voice-settings.png) |
| Privacy | Perception/Retention/Actions sections; source editing and technical details on demand; independent grants/revoke preserved | [Privacy](screens/review-privacy.png) |
| Memory | Core ownership and unavailable phone tools; encrypted draft explanation on demand | [Memory](screens/review-memory.png) |
| Android permissions | Actual assistant selection and its scope; unavailable platform features behind details | [Android permissions](screens/review-android.png) |
| Notifications | Actual alert grant, task alert toggle and reply entry; no duplicate page heading | [Notifications](screens/review-notifications.png) |
| Appearance | Theme and reduced-motion controls; one short accessibility explanation | [Appearance](screens/review-appearance.png) |
| Diagnostics | Connection, observation, task availability and version; implementation notes behind details | [Diagnostics](screens/review-diagnostics.png) |
| About | OSCAR/version first; privacy/setup and public identity behind details | [About](screens/review-about.png) |
| Connection dialog | Short setup instructions, labelled fields, masked token and visible source-change warning; empty Connect disabled | [Connection](screens/review-connection.png) |

The route inventory is exercised by `AppReviewTest` using actual production
navigation. It also checks the single-toolbar/Back/tab structure, nested return
paths, the disabled empty connection form and Voice cancellation back to the
preserved composer. Existing tests cover rich responses, decision review/expiry,
actual disposable Core/Grid loss/reconnect, privacy revocation, encrypted draft
recovery, dark mode, 1.8× text, keyboard avoidance, landscape and reduced motion.
The final supplemental receipt is `app-review.json`; `verification.json` and
`devices-review.json` retain the earlier, separately identified runs.

Captures are native Samsung SM-S721B/API36 rendering from the explicitly opted-in
review package with separate app data. Core/task/decision examples are synthetic.
The contact sheets support visual inspection; full-resolution originals remain
linked above. No owner conversation, notification, credential or recording is
captured. Owner visual approval, real audio, biometric confirmation and Android
integration commissioning remain separate acceptance work.
