# Implemented Conversation review — actual native windows

[Paper light](conversation-light.png) · [Warm graphite dark](conversation-dark.png)

These are actual bundled Tauri/WebView2 HWND captures, not Image Gen concepts.
The implementation uses the existing shared expression renderer at the bottom
of the sidebar, an accessible icon-only Send button, a compact type scale and
an anchored composer outside the scrolling conversation. Companion is unchanged.
Theme choice updates the native caption and the shared native View. Ordinary
product runs persist appearance and shortcut choices in native configuration;
the disposable review harness isolates owner preferences. No authority or
separate assistant store is introduced.

The read-only design research used [the official Codex app screenshot](https://developers.openai.com/images/codex/app/codex-app-basic-light.webp)
for density and [Fluent spacing](https://fluent2.microsoft.design/layout) /
[typography](https://fluent2.microsoft.design/typography) for native hierarchy.
OSCAR keeps its own canonical paper/ink/identity palette and feature contracts.
No reference product's chat/project/plugin/model features were copied.

The [receipt](receipt.json) checks both native theme projections, computed theme
tokens, the exact shared Orb renderer and visible composer. Content is explicitly
SCRIPTED / REPORTED from the authenticated disposable Core; it is not inference
or owner acceptance. Native capture waits for the WebView/non-client repaint.

An independent GPT-6.1 Sol / Medium reviewer inspected both captures and found
no material visual issues at this scope. It suggested an optional reduction in
paragraph spacing; broad refinement was not added. Owner visual acceptance,
keyboard/contrast/resize matrix and remaining page acceptance stay separate.

Reproduce after building the existing debug Tauri app:

```powershell
python -m scripts.desktop_conversation_review
```

All prior Image Gen comparisons are unapproved history. The current native
Conversation view is the next owner design checkpoint, not a completed Group
2.5A candidate or draft-PR claim.
