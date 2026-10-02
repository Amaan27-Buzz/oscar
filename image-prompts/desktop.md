# Desktop Prompts

Use the global rules in `image-prompts/README.md`.

## Desktop — compact presence

Design OSCAR as a small native desktop presence on Windows/macOS.

The surface should feel ambient rather than like a full app. A compact OSCAR presence object, current state and one contextual interaction affordance are enough. It should be able to expand fluidly when invoked.

No permanent chat sidebar. No giant floating assistant window. Use warm neutral materials, graphite text and restrained OSCAR blue/yellow.

## Desktop — Ask current context

Design the compact overlay after the user invokes Ask on the current screen/cursor target.

The overlay should visually attach to the target/context rather than float randomly. Show one concise question/answer state, current app/context indicator and a small route to deeper evidence if needed.

OSCAR should feel like part of the operating environment.

## Desktop — selected-text Edit

Design an OSCAR overlay attached to selected text in another application.

Show the selected-text relationship, a concise rewrite/edit instruction, preview and accept/revert controls. Keep the surrounding app context visible. Avoid a large chat window.

## Desktop — Act

Design a compact OSCAR Act state while operating the current application through an appropriate capability.

Show the objective, current action, executor/capability and truthful state such as `Working` or `Waiting for approval`. Keep controls minimal: pause/cancel/inspect where appropriate.

## Desktop — Working → Verifying

Design a two-state visual reference showing how the same compact task surface physically transforms from `Working` to `Verifying`.

Shared geometry should persist. `Verifying` must feel more deliberate/tight, not like generic loading. Do not show success until evidence is checked.

## Desktop — remote continuation

Design the desktop side of a task that will continue after the user leaves.

Show a long-running Codex/build/render process attached to OSCAR Durable Execution Runtime. Offer a concise option such as `Keep running when I leave` or policy state, plus remote visibility through Sunday.

The interface should make it obvious the task can outlive the user's physical presence without making the PC OSCAR's host.

## Desktop — verified completion and shutdown option

Design a task-complete surface after OSCAR has verified the expected output.

Show result/artifact, verification evidence summary, and a contextual action such as `Shut down this PC` only if supported and already permitted. Avoid celebratory UI.

## Desktop — expanded OSCAR workspace

Design the larger native OSCAR window used when deeper management is actually needed.

It may contain active tasks, Workers, meaningful history, artifacts, Connection Grid and settings, but avoid dashboard gravity. Use one dominant current objective and progressive disclosure for everything else.

No wall of cards or KPI tiles.

## Desktop — Connection Grid

Design the Connection Grid from desktop.

Show current nodes and capability availability with a restrained operational composition: Sunday, cloud coordinator, this desktop, Edge and any other paired node. The user should understand where work is running and which nodes are offline without seeing a network-admin console.

## Desktop — provider/router usage

Design the native OSCAR provider/model routing surface.

Show Auto/Balanced/Heavy/etc. mode, connected model providers, masked credential pools, health, recent routes and why a model was selected. Keep advanced usage/cost/quota detail behind disclosure.

Do not use analytics-dashboard styling.

## Desktop — computer use / installed app

Design OSCAR controlling an installed application using the strongest available legitimate integration path.

Show current app, selected capability (`native API`, `CLI`, `accessibility`, or `computer use`), task intent, permission state and real progress. Keep it clear that computer use is a fallback, not magic unrestricted control.

## Desktop — blocked/degraded

Design a task that became blocked because the executor/app/node disappeared.

Show `Blocked`, why, what OSCAR can recover automatically, and one user action only if genuinely needed. Do not show `Thinking` or `Working` after terminal failure.
