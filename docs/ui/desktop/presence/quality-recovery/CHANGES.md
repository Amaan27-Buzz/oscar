# Implementation and design changes

The original compact concept remains a character with a writing leaf. This
correction makes its request outcomes understandable and its window reversals
reliable, while giving owner attention and active movement greater clarity.
It does not replace the concept with a chat window or redesign Ask/Edit/Act.

## Trustworthy interaction

Specific no-task blockers now survive Core → native bridge → fresh expression
readback → composition. Missing capability, denied permission, rejection and
uncertain transport outcome stay distinct. Inspect/check actions never silently
resubmit a request. Editing preserves the draft and previous reason. Core tasks,
Action Ledger actions and signed native reviews still own execution authority.

Duplicate window event/reply acknowledgement is accepted as confirmation of the
same actual window state. Invocation cancels obsolete retreat work; successful
native recovery clears presentation errors without clearing unresolved Core
failures. Snapshot freshness is checked before replacing the current task, and
expired/completed native approval material is retired.

## Composition

The writing leaf is 432 × 416 logical pixels, 32 taller than the original.
Compact remains 132 × 148 with the same bottom-right character anchor. A smaller
22 px heading gives operational reasons room; body 15 px, secondary 12 px and
compact caption 12 px improve small-size legibility. A restrained asymmetric
leaf corner connects visually to the Orb. Focus stays inside the compact bounds.
No new pills, icon strip, glass, gradients or dashboard are introduced.

Owner attention has an awake asymmetric pose, yellow caption, direct heading,
the submitted request bound to the actual task, and one dominant **Review
decision** action. Local submitted text is explicitly labelled; it never stands
in for the full authoritative review. Other tasks use their Core description.
**Leave pending** retreats without making a decision. The existing Activity
workspace gains a return to presence and retains request feedback.
The fresh reviewer then found that the review section was below the initial
workspace viewport. A presence-only opt-in now focuses and scrolls the exact
authoritative section once per review id; default App behavior remains unchanged.

## Character and motion

The shared arbitration previously replaced explicit quiet/curious delivery with
attentive and subdued owner waiting. It now preserves quiet character choices
and keeps owner waiting visibly attentive, identically in TypeScript and Kotlin.
Existing shared spring, gaze, asymmetric eyes, puck translation/rotation and
engagement phrase are reused. A fresh real executing transition admits one
finite engagement accent after 70 ms; polling does not replay it. New operational
state interrupts it through the existing controller. Rest remains still; reduced
motion remains functional. No second animation engine or activity claim exists.

## Architecture and scope

`oscar/desktop.py` adds explanatory reason metadata only; `oscar/mobile.py`
distinguishes permission HTTP rejection. Native `core.rs` validates/bounds
responses and supplies additive feedback/window revision/task-bound reviews.
`DesktopExpressionAdapter` supplies fresh operational truth to the shared
Expression Controller. `LivingPresence` owns local draft, presentation intent,
gaze and surrounding composition. Native Tauri continues to own window actions.

The normal production entry point, UI composition and prototype exclusion remain
unchanged; release does not promote this presence. **Shared expression arbitration
and HTTP feedback improvements do reach existing renderers/clients.** Do not
interpret prototype isolation as a claim that every production pixel is identical.
Canonical `assets/brand/oscar-orb.svg` is unchanged. Core policy, contracts and
signed approval authority are preserved. No new dependency, CI configuration,
model training, real speech commissioning or Slice 12.2 work.
