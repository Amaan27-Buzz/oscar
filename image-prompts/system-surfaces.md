# System Surface Prompts

Use the global rules in `image-prompts/README.md`.

## Onboarding — welcome / product model

Design OSCAR's first commissioning screen.

Explain through composition, not a paragraph: one intelligence across OSCAR Mobile, desktop, cloud and Edge. Use a small OSCAR presence object, one calm headline and a simple visual relationship between embodiments.

The screen should feel like commissioning personal infrastructure, not signing up for another app.

## Onboarding — Persona

Design the setup moment where the user chooses OSCAR's initial character.

Offer a few original starting profiles such as Wry, Steady, Spark, Formal and Custom, with concise trait previews. Also provide `Describe how you want OSCAR to act` as the natural-language path.

Make clear that truthfulness/safety are fixed while humor, candor, warmth, formality, brevity and playfulness can change.

## Onboarding — Voice / Voice Match / Voice Map

Design one grouped setup surface that clearly separates:
- OSCAR Voice Identity;
- Voice Match = authorization signal;
- Voice Map = perception of who appears to be speaking.

Use progressive disclosure. Avoid biometric-security theatre.

## Onboarding — Sentry / daily capture privacy

Design the setup page for persistent Sentry awareness and optional continuity capture.

Show three conceptually different levels:
- Awareness only;
- Context capture;
- Daily journal.

Separate local wake/VAD, speaker recognition, transcription, raw audio retention and transcript retention. Make consent/retention obvious without overwhelming the user.

## Onboarding — Connection Grid

Design setup for OSCAR Mobile, cloud coordinator, desktop and Edge pairing.

Show each node joining OSCAR with a verified/partial/unavailable state. Include optional free/paid cloud choice without turning setup into cloud-infrastructure administration.

The final state should communicate resilient availability rather than one required host.

## Persona — advanced detail

Design a deeper Persona profile editor.

Use a small set of refined sliders/controls for Humor, Candor, Warmth, Formality, Brevity, Playfulness, Initiative and Pushback, plus context triggers such as `security alert → serious` and `university call → formal`.

Truthfulness should be visibly fixed/non-configurable.

## Workers — overview

Design a minimal Worker visibility surface.

Show only a few delegated responsibilities with meaningful states such as Active, Waiting, Verifying and Blocked. Each Worker should show responsibility and current meaningful action rather than agent metrics.

No agent-management dashboard.

## Worker — detail

Design one Worker detail view showing responsibility, current action, executor/capability, autonomy scope, approvals, artifact/result and blocker/evidence state.

Make `reported success` visually distinct from `verified`.

## Memory

Design OSCAR's memory/history surface.

Show a searchable continuous timeline of meaningful remembered context with source/provenance and correction/forget controls on demand. Do not expose vector-database mechanics.

## Personal Policy

Design a Personal Policy screen clearly distinct from memory.

Show a few natural-language rules, scope and whether each is active. Include conversational creation such as `Never reveal calendar event names` and a compact explanation of which policy affected an action.

## Daily Journal / continuity history

Design a unified daily continuity view for explicitly enabled capture.

Combine calls, messages/mail, meetings and in-person conversation summaries into one chronological day view while preserving source labels and privacy/retention boundaries. Raw audio should not dominate the UI.

Allow `Pause capture`, `Forget this`, and source/retention inspection.

## Communication — incoming call

Design an incoming call flow where OSCAR evaluates caller context and Personal Policy.

Show what OSCAR is allowed to do, not capabilities it merely wishes it had. Keep actions concise and native to mobile/desktop context.

## Communication — call / meeting summary

Design a post-call or meeting result surface with summary, decisions, action items and follow-up state. Speaker identity should remain confidence-qualified where relevant.

Keep one dominant summary and progressively reveal transcript/evidence.

## World Model — current awareness

Design a user-facing `What OSCAR knows right now` surface.

Show current devices, environment and active context in an understandable human layout, not a science-fiction graph. Include freshness/source only when expanded.

## Devices / Edge

Design a native device capability page for a paired Edge node.

Show identity, health, available sensors/actions, one current physical state and safe controls. Hide raw GPIO/technical details until advanced view.

## Connection Grid — availability failure

Design the Grid during partial outage: cloud unavailable, OSCAR Mobile still present, desktop task continuing locally, Edge healthy.

Communicate graceful degradation with explicit availability state such as `Local` rather than a generic offline error. Show what continues to work and what is queued.

## Action Ledger

Design a human-readable consequential-action history.

Show examples such as message sent, files changed, device action or meeting scheduled. Each entry can reveal initiator, permission/policy, result, verification and real Undo only when supported.

Avoid audit-log aesthetics in the default view.

## Approval

Design a concise sensitive-action approval surface.

Show consequence, target, why OSCAR is asking, and clear approve/deny. For critical actions include OSCAR Mobile biometric/PIN requirement. Do not bury the consequence in prose.

## Failure / self-recovery

Design OSCAR recovering from an ordinary failure automatically.

Example: provider unavailable → route switched safely → task continues. Show calm state progression and only interrupt the user if the recovery cannot continue.

## Avatar state reference

Create a restrained design-development state sheet for the OSCAR presence object showing Idle, Listening, Speaking, Working, Verifying, Waiting, Blocked, Done, Sentry, Muted and Offline.

This is a development reference, not an in-product page. Keep expressions minimal and let puck position/motion imply state. Do not make it a cartoon emotion sheet.
