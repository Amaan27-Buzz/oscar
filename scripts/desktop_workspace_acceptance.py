"""Actual bundled Tauri/WebView2 two-surface checks against a disposable authenticated Core.

Captures only launched native HWNDs. No owner app, audio, credentials or physical PASS.
"""

import ctypes
import hashlib
import json
import subprocess
import time
from ctypes import wintypes
from pathlib import Path

from playwright.sync_api import sync_playwright

from scripts.desktop_baseline import capture_owned, windows
from scripts.desktop_native_fixture import native_fixture

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/ui/desktop/interaction-polish/evidence"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, condition):
        assert condition, name
        checks.append(name)
        print("PASS", name, flush=True)

    with native_fixture(workspace=True) as (info, lines, command), sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{info['native_debug_port']}")
        pages = [p for c in browser.contexts for p in c.pages]
        companion = next(p for p in pages if "?companion" in p.url)
        workspace = next(p for p in pages if "?companion" not in p.url)
        companion.get_by_text("Disconnected", exact=True).wait_for(state="hidden", timeout=20000)

        def handle(title):
            return next(h for h, _, t in windows(info["pid"]) if t == title)

        def shot(page, name, title):
            if title == "OSCAR Workspace":
                selected = {
                    "workspace-home": "Conversation",
                    "conversation": "Conversation",
                    "reading": "Conversation",
                    "devices": "Devices",
                    "actions": "Automations",
                    "privacy": "Preferences",
                    "preferences": "Preferences",
                    "preferences-narrow": "Preferences",
                    "activity-working": "Activity",
                    "approval": "Activity",
                }.get(name)
                if selected:
                    page.get_by_role("navigation", name="Workspace").get_by_role(
                        "button", name=selected, exact=True
                    ).click()
            if title == "OSCAR Workspace":
                invoke(page, "surface_command", {"kind": "theme", "theme": "light"})
                page.wait_for_function("document.documentElement.dataset.theme==='light'")
            if title == "OSCAR Workspace":
                page.locator(".workspace-content").evaluate("el=>el.scrollTop=0")
            page.wait_for_timeout(350)
            result = capture_owned(info["pid"], handle(title), OUTPUT / f"{name}.png")
            if title == "OSCAR Workspace":
                axes = page.evaluate("""()=>{
                    const body=document.querySelector('.workspace-body').getBoundingClientRect();
                    const header=document.querySelector('.workspace-top-inner')
                        .getBoundingClientRect();
                    return Math.abs((header.left-body.left)-(body.right-header.right))<1.5;
                }""")
                check(f"{name}: header has balanced edge spacing", axes)
                for theme in ("dark", "light"):
                    invoke(page, "surface_command", {"kind": "theme", "theme": theme})
                    page.wait_for_function(
                        "theme=>document.documentElement.dataset.theme===theme", arg=theme
                    )
                    page.wait_for_timeout(400)
                    if theme == "dark":
                        capture_owned(info["pid"], handle(title), OUTPUT / f"{name}-dark.png")
            return result

        def invoke(page, name, request):
            return page.evaluate(
                """async ([name,request])=>{
                  try{const value=await window.__TAURI_INTERNALS__.invoke(name,{request});
                    return {ok:true,value};}
                  catch(e){return {ok:false,error:String(e)};}
                }""",
                [name, request],
            )

        check("two WebViews share one native process", len(pages) == 2)
        check(
            "Companion denies Desktop commands",
            not invoke(companion, "desktop_command", {"kind": "refresh"})["ok"],
        )
        denied = companion.evaluate(
            """async()=>{try{
              await window.__TAURI_INTERNALS__.invoke('plugin:event|listen',{
                event:'desktop-state',target:{kind:'Any'},handler:0});return false;
            }catch{return true;}}"""
        )
        check("Companion cannot listen to private Workspace events", denied)
        check(
            "Companion cannot change Workspace appearance",
            not invoke(companion, "surface_command", {"kind": "theme", "theme": "dark"})["ok"],
        )
        state = invoke(companion, "surface_command", {"kind": "ready"})["value"]
        check(
            "Companion projection has no private material",
            state["context"] is None
            and state["review"] is None
            and state["preview"] is None
            and not state["capabilities"]
            and not state["conversation"]["turns"]
            and state["operating"] is None,
        )
        shot(companion, "companion-idle", "OSCAR Companion")
        companion.get_by_role("button", name="Open OSCAR Workspace", exact=True).click()
        workspace.get_by_role("region", name="Conversation scroll area").wait_for()
        shot(workspace, "workspace-home", "OSCAR Workspace")
        check(
            "no redundant conversation heading",
            workspace.get_by_role("heading", name="Conversation", exact=True).count() == 0,
        )
        check(
            "unavailable voice is absent from composer",
            workspace.get_by_role("button", name="Use voice", exact=True).count() == 0,
        )

        check(
            "product surface has no development banner",
            workspace.locator(".workspace-reference").count() == 0,
        )
        check(
            "composer has no resize handle",
            workspace.get_by_label("Ask OSCAR").evaluate(
                "el=>getComputedStyle(el).resize==='none'"
            ),
        )
        check(
            "controls use no inset button shadows",
            workspace.evaluate("""()=>
            [...document.querySelectorAll('.workspace button')].every(
                el=>!getComputedStyle(el).boxShadow.includes('inset'))"""),
        )
        workspace.get_by_label("Ask OSCAR").fill("2 + 3")
        workspace.get_by_role("button", name="Send", exact=False).click()
        companion.get_by_text("Review needed", exact=True).wait_for(timeout=15000)
        shot(companion, "companion-attention", "OSCAR Companion")
        shot(workspace, "conversation", "OSCAR Workspace")
        for theme in ("light", "dark"):
            invoke(workspace, "surface_command", {"kind": "theme", "theme": theme})
            workspace.get_by_role("navigation", name="Workspace").get_by_role(
                "button", name="Conversation", exact=True
            ).click()
            workspace.locator(".conversation-thread-inner").wait_for()
            check(
                theme + ": owner messages align right and replies left",
                workspace.evaluate(
                    """()=>{const column=document.querySelector('.conversation-thread-inner');
                const owner=column.querySelector('.user-turn');
                const reply=column.querySelector('.assistant-turn');
                const o=owner.getBoundingClientRect(),r=reply.getBoundingClientRect();
                return o.left>r.left+40&&Math.abs(o.right-r.right)<2&&o.width<=r.width*.8}"""
                ),
            )

        companion.get_by_role(
            "button", name="Open Workspace — owner attention required", exact=True
        ).click()
        workspace.get_by_role("heading", name="Activity", exact=True).wait_for()
        attention_state = invoke(workspace, "desktop_command", {"kind": "ready"})["value"]
        check(
            "Companion attention opens work without granting approval",
            attention_state["current"]["state"] == "planned" and attention_state["review"] is None,
        )
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Conversation", exact=True
        ).click()
        workspace.get_by_label("Ask OSCAR").fill("Unsent keyboard review draft")
        workspace.keyboard.press("Tab")
        check(
            "keyboard reaches icon-only Send from the composer",
            workspace.evaluate("document.activeElement.getAttribute('aria-label')==='Send'"),
        )
        workspace.keyboard.press("Shift+Tab")
        check(
            "keyboard returns to the editable draft",
            workspace.evaluate("document.activeElement.id==='workspace-ask'"),
        )
        for theme in ("light", "dark"):
            invoke(workspace, "surface_command", {"kind": "theme", "theme": theme})
            workspace.wait_for_timeout(200)
            contrast = workspace.evaluate("""()=>{
                const style=getComputedStyle(document.documentElement);
                const rgb=name=>{let hex=style.getPropertyValue(name).trim().slice(1);
                    if(hex.length===3)hex=[...hex].map(c=>c+c).join('');
                    return hex.match(/../g).map(x=>parseInt(x,16)/255)};
                const lum=name=>rgb(name).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4)
                    .reduce((s,x,i)=>s+x*[.2126,.7152,.0722][i],0);
                const ratio=(a,b)=>{a=lum(a);b=lum(b);
                    return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
                return {body:ratio('--text','--desk'),metadata:ratio('--muted','--desk'),
                    sidebar:ratio('--muted','--rail'),button:ratio('--on-primary','--primary')};
            }""")
            check(
                f"{theme}: body, metadata, sidebar and primary text contrast meet 4.5:1",
                all(value >= 4.5 for value in contrast.values()),
            )
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Conversation", exact=True
        ).click()
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Preferences", exact=True
        ).click()
        workspace.get_by_role("button", name="Advanced controls", exact=True).click()
        workspace.get_by_role("tab", name="Dictate", exact=True).focus()
        workspace.keyboard.press("ArrowRight")
        workspace.wait_for_timeout(200)
        check(
            "keyboard text-mode navigation retains selected tab focus",
            workspace.get_by_role("tab", name="Edit", exact=True).get_attribute("aria-selected")
            == "true"
            and workspace.evaluate("document.activeElement.id==='tool-Edit'"),
        )
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Conversation", exact=True
        ).click()
        current = invoke(workspace, "desktop_command", {"kind": "ready"})["value"]["current"]
        task = current["task_id"]
        invoke(
            workspace,
            "desktop_command",
            {"kind": "review", "task_id": task, "operation": "approve"},
        )
        workspace.get_by_role("button", name="Continue to confirmation").wait_for()
        shot(workspace, "approval", "OSCAR Workspace")
        # Programmatic fixture progression is explicitly separate from human native confirmation.
        command("execute")
        workspace.get_by_text("Running", exact=True).first.wait_for(timeout=15000)
        companion.get_by_text("Running", exact=True).wait_for(timeout=15000)
        shot(companion, "companion-working", "OSCAR Companion")
        shot(workspace, "activity-working", "OSCAR Workspace")
        check(
            "Activity row has balanced inset and no oversized strip",
            workspace.locator(".activity-list button").first.evaluate(
                """el=>{const s=getComputedStyle(el),r=el.getBoundingClientRect();
                const a=el.querySelector('span').getBoundingClientRect();
                const b=el.querySelector('small').getBoundingClientRect();
                return a.left-r.left>=12&&r.right-b.right>=12
                    &&r.height<65&&s.boxShadow==='none'}"""
            ),
        )

        command("finish")
        workspace.get_by_text("Verified", exact=True).first.wait_for(timeout=15000)
        check(
            "shared task survives progression",
            invoke(workspace, "desktop_command", {"kind": "ready"})["value"]["current"]["task_id"]
            == task,
        )
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Conversation", exact=True
        ).click()
        check(
            "actual arithmetic outcome",
            workspace.locator(".assistant-turn").filter(has_text="5").count() > 0,
        )
        companion.locator(".companion-orb").hover()
        companion.wait_for_timeout(350)
        dimensions = shot(companion, "companion-controls", "OSCAR Companion")
        check(
            "Companion retains 148 by 164 logical size",
            dimensions["logical_width"] == 148 and dimensions["logical_height"] == 164,
        )
        check(
            "five toolbar controls fit the real window",
            companion.evaluate(
                """()=>[...document.querySelectorAll('.companion-icon-row button')].every(el=>{
                const r=el.getBoundingClientRect();
                return r.left>=0&&r.right<=innerWidth&&r.bottom<=innerHeight})"""
            ),
        )

        check(
            "voice is unavailable without a permissioned adapter",
            companion.get_by_role("button", name="Use voice", exact=True).is_disabled(),
        )
        check(
            "Sentry is unavailable",
            invoke(companion, "surface_command", {"kind": "ready"})["value"]["voice_support"][
                "sentry"
            ]
            == "unavailable",
        )
        check(
            "Workspace cannot open Companion-native menu",
            not invoke(workspace, "surface_command", {"kind": "companion_menu"})["ok"],
        )
        invoke(companion, "surface_command", {"kind": "shortcut_enabled", "enabled": False})
        check(
            "shortcut disable is native",
            not invoke(workspace, "desktop_command", {"kind": "ready"})["value"][
                "shortcut_enabled"
            ],
        )
        invoke(companion, "surface_command", {"kind": "shortcut_enabled", "enabled": True})
        check(
            "shortcut is only in overflow",
            companion.get_by_role("button", name="Shortcut on").count() == 0,
        )
        user = ctypes.WinDLL("user32")
        user.PostMessageW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user.GetDpiForWindow.argtypes = [wintypes.HWND]
        work = wintypes.RECT()
        user.SystemParametersInfoW(48, 0, ctypes.byref(work), 0)
        scale = user.GetDpiForWindow(handle("OSCAR Companion")) / 96
        user.SetWindowPos(
            handle("OSCAR Companion"),
            None,
            work.right - round(160 * scale),
            work.bottom - round(170 * scale),
            0,
            0,
            0x0005,
        )
        user.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        user.SetForegroundWindow.argtypes = [wintypes.HWND]
        invoke(workspace, "surface_command", {"kind": "open_workspace"})
        workspace.wait_for_timeout(500)
        user.GetForegroundWindow.restype = wintypes.HWND
        check(
            "Workspace receives real native focus",
            user.GetForegroundWindow() == handle("OSCAR Workspace"),
        )
        check(
            "focused Workspace is not obscured by always-on-top Companion",
            not user.GetWindowLongW(handle("OSCAR Companion"), -20) & 8,
        )
        check(
            "Companion reads Ask from Core without authority material",
            state["access_mode"] == "Ask" and state["operating"] is None,
        )
        for kind, name in (
            ("access_menu", "access-selector"),
            ("sentry_menu", "sentry-selector"),
            ("companion_menu", "overflow"),
        ):
            check(
                kind + ": Workspace caller denied",
                not invoke(workspace, "surface_command", {"kind": kind})["ok"],
            )
            menus = []
            for _attempt in range(3):
                user.SetForegroundWindow(handle("OSCAR Companion"))
                companion.wait_for_timeout(250)
                companion.evaluate(
                    "kind=>{void window.__TAURI_INTERNALS__.invoke("
                    "'surface_command',{request:{kind}})}",
                    kind,
                )
                companion.wait_for_timeout(350)
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    menus = [h for h, c, _ in windows(info["pid"]) if c == "#32768"]
                    if menus:
                        break
                    time.sleep(0.1)
                if menus:
                    break
            check(kind + ": real native popup exists", bool(menus))
            if menus:
                rect = wintypes.RECT()
                assert user.GetWindowRect(menus[0], ctypes.byref(rect)), (
                    "Popup closed before inspection"
                )
                work = wintypes.RECT()
                user.SystemParametersInfoW(48, 0, ctypes.byref(work), 0)
                print(
                    "POPUP",
                    kind,
                    tuple(getattr(rect, k) for k in ("left", "top", "right", "bottom")),
                    "WORK",
                    tuple(getattr(work, k) for k in ("left", "top", "right", "bottom")),
                    flush=True,
                )
                check(
                    kind + ": popup fits work area near taskbar",
                    rect.right > rect.left
                    and rect.bottom > rect.top
                    and rect.left >= work.left
                    and rect.top >= work.top
                    and rect.right <= work.right
                    and rect.bottom <= work.bottom,
                )
                capture_owned(info["pid"], menus[0], OUTPUT / (name + ".png"))
            user.keybd_event(0x1B, 0, 0, 0)
            user.keybd_event(0x1B, 0, 2, 0)
            workspace.wait_for_timeout(250)
            check(
                kind + ": Escape dismisses native popup",
                not any(c == "#32768" for _, c, _ in windows(info["pid"])),
            )
        reserved = user.RegisterHotKey(None, 24131, 0x4003, 0x5A)
        assert reserved, "Disposable collision reservation failed"
        try:
            collision = invoke(
                workspace, "desktop_command", {"kind": "shortcut", "accelerator": "Ctrl+Alt+Z"}
            )
            check(
                "shortcut collision is reported and retains invocation",
                not collision["ok"]
                and "collision" in collision["error"].lower()
                and invoke(workspace, "desktop_command", {"kind": "ready"})["value"]["shortcut"]
                == "Ctrl+Alt+O",
            )
        finally:
            user.UnregisterHotKey(None, 24131)
        hwnd = handle("OSCAR Workspace")
        user.PostMessageW(hwnd, 0x0010, 0, 0)
        workspace.wait_for_timeout(600)
        check(
            "hidden Workspace restores Companion desktop presence",
            bool(user.GetWindowLongW(handle("OSCAR Companion"), -20) & 8),
        )
        check(
            "native close hides only Workspace",
            not any(t == "OSCAR Workspace" for _, _, t in windows(info["pid"]))
            and any(t == "OSCAR Companion" for _, _, t in windows(info["pid"])),
        )
        # System key input does not focus Companion. Global invocation must reveal Workspace.
        for key in (0x11, 0x12, 0x4F):
            user.keybd_event(key, 0, 0, 0)
        for key in (0x4F, 0x12, 0x11):
            user.keybd_event(key, 0, 2, 0)
        workspace.wait_for_timeout(1000)
        check(
            "global shortcut reveals hidden Workspace",
            any(t == "OSCAR Workspace" for _, _, t in windows(info["pid"])),
        )
        check(
            "task continuity after native close and hotkey",
            invoke(workspace, "desktop_command", {"kind": "ready"})["value"]["current"]["task_id"]
            == task,
        )
        shot(workspace, "workspace-reopened", "OSCAR Workspace")
        invoke(workspace, "surface_command", {"kind": "hide_companion"})
        check(
            "Companion hides independently",
            not any(t == "OSCAR Companion" for _, _, t in windows(info["pid"])),
        )
        invoke(workspace, "surface_command", {"kind": "show_companion"})
        check(
            "Companion returns without replacing tasks",
            any(t == "OSCAR Companion" for _, _, t in windows(info["pid"])),
        )
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Conversation", exact=True
        ).click()
        check(
            "session conversation preserves the first turn",
            "2 + 3" in workspace.locator(".conversation-thread").inner_text(),
        )
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Preferences", exact=True
        ).click()
        workspace.get_by_label("Context from other apps", exact=True).click()
        workspace.get_by_role("radio", name="Selected text", exact=True).click()
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Conversation", exact=True
        ).click()
        check(
            "conversation has no tool or memory implementation UI",
            all(
                workspace.get_by_text(label, exact=False).count() == 0
                for label in (
                    "Canonical history",
                    "Private session",
                    "Saved reply",
                    "Dictate or edit",
                    "Prepare an action",
                )
            ),
        )
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Preferences", exact=True
        ).click()
        check(
            "capture preference survives navigation",
            workspace.get_by_label("Context from other apps", exact=True).get_attribute(
                "data-value"
            )
            == "selection",
        )
        workspace.get_by_label("Context from other apps", exact=True).click()
        workspace.get_by_role("radio", name="Don’t include app context", exact=True).click()
        shot(workspace, "privacy", "OSCAR Workspace")
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Devices", exact=True
        ).click()
        check(
            "Devices hides provider vocabulary behind details",
            workspace.get_by_role("button", name="Find information", exact=True).is_visible()
            and workspace.get_by_text("Provider-native", exact=False).count() == 0,
        )
        shot(workspace, "devices", "OSCAR Workspace")

        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Automations", exact=True
        ).click()
        check(
            "Automations does not fabricate scheduled Workers",
            workspace.get_by_text(
                "Ongoing routines and watches aren’t available yet.", exact=False
            ).is_visible(),
        )
        shot(workspace, "actions", "OSCAR Workspace")
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Preferences", exact=True
        ).click()
        operating = invoke(workspace, "desktop_command", {"kind": "ready"})["value"]["operating"]
        check(
            "Core keeps independent dimensions",
            operating["access"] == "Ask"
            and operating["awareness"] == "Trigger-only"
            and operating["worker_autonomy"] == "Manual",
        )
        workspace.get_by_role("button", name="Access modes", exact=True).click()
        check(
            "Full Access remains unrestricted and unavailable",
            workspace.get_by_text(
                "means unrestricted owner-delegated autonomy", exact=False
            ).is_visible()
            and workspace.get_by_text("Not available yet.", exact=False).count() >= 2,
        )
        shot(workspace, "preferences", "OSCAR Workspace")
        invoke(workspace, "surface_command", {"kind": "hide_workspace"})
        companion.get_by_role("button", name="Open OSCAR Workspace", exact=True).click()
        workspace.get_by_role("heading", name="Preferences", exact=True).wait_for()
        check("ordinary reopen preserves the owner-selected page", True)
        command("long")
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Conversation", exact=True
        ).click()
        workspace.get_by_label("Ask OSCAR").fill("Explain a disposable reference")
        workspace.get_by_role("button", name="Send", exact=False).click()
        companion.get_by_text("Review needed", exact=True).wait_for(timeout=15000)
        command("execute")
        workspace.get_by_text("Running", exact=True).first.wait_for(timeout=15000)
        command("finish")
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Conversation", exact=True
        ).click()
        workspace.locator(".retained-turn").filter(has_text="A scripted reference answer").wait_for(
            timeout=15000
        )
        shot(workspace, "reading", "OSCAR Workspace")
        check(
            "reading preserves reported truth",
            any(
                t["status"] == "REPORTED"
                for t in invoke(workspace, "desktop_command", {"kind": "ready"})["value"][
                    "conversation"
                ]["turns"]
            )
            and "REPORTED" not in workspace.locator(".conversation-thread").inner_text(),
        )
        command("disconnect")
        companion.get_by_text("Disconnected", exact=True).wait_for(timeout=15000)
        shot(companion, "companion-unavailable", "OSCAR Companion")
        shot(workspace, "workspace-unavailable", "OSCAR Workspace")
        check(
            "offline disables new work",
            workspace.get_by_role("button", name="Send", exact=False).is_disabled(),
        )
        command("reconnect")
        companion.get_by_text("Disconnected", exact=True).wait_for(state="hidden", timeout=15000)
        check(
            "Core reconnect restores shared tasks",
            len(invoke(workspace, "desktop_command", {"kind": "ready"})["value"]["tasks"]) >= 2,
        )
        workspace.emulate_media(reduced_motion="reduce")
        check(
            "reduced motion supported",
            workspace.evaluate("matchMedia('(prefers-reduced-motion:reduce)').matches"),
        )
        # Exercise real native resizing and measure resulting geometry in both themes.
        user.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user.GetDpiForWindow.argtypes = [wintypes.HWND]
        current_scale = user.GetDpiForWindow(handle("OSCAR Workspace")) / 96
        user.SetWindowPos(
            handle("OSCAR Workspace"),
            None,
            0,
            0,
            round(800 * current_scale),
            round(620 * current_scale),
            0x0006,
        )
        workspace.wait_for_timeout(400)
        for item in ("Conversation", "Automations", "Activity", "Devices", "Preferences"):
            workspace.get_by_role("navigation", name="Workspace").get_by_role(
                "button", name=item, exact=True
            ).click()
            for theme in ("light", "dark"):
                invoke(workspace, "surface_command", {"kind": "theme", "theme": theme})
                workspace.wait_for_timeout(150)
                check(
                    f"{item} {theme}: narrow native layout has no horizontal overflow",
                    workspace.evaluate("""()=>[...document.querySelectorAll(
                        '.workspace,.workspace-body,.workspace-content')].every(
                        el=>el.scrollWidth<=el.clientWidth+1)"""),
                )
        shot(workspace, "preferences-narrow", "OSCAR Workspace")
        user.SetWindowPos(
            handle("OSCAR Workspace"),
            None,
            0,
            0,
            round(1180 * current_scale),
            round(850 * current_scale),
            0x0006,
        )
        workspace.wait_for_timeout(300)
        workspace.get_by_role("navigation", name="Workspace").get_by_role(
            "button", name="Conversation", exact=True
        ).click()
        # Continuous native capture stream, side-by-side owned HWNDs, during real transitions.
        from PIL import Image, ImageDraw

        frames = ROOT / f".oscar/group25-recording/{time.time_ns()}"
        frames.mkdir(parents=True, exist_ok=True)

        def record(seconds, label):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                canvas = Image.new("RGB", (1440, 940), "#0b1016")
                draw = ImageDraw.Draw(canvas)
                draw.text(
                    (22, 20), "Actual native Tauri / disposable Core / " + label, fill="white"
                )
                for title, x, y in [("OSCAR Companion", 20, 100), ("OSCAR Workspace", 230, 65)]:
                    matches = [h for h, _, t in windows(info["pid"]) if t == title]
                    if matches:
                        file = frames / "capture.png"
                        capture_owned(info["pid"], matches[0], file)
                        pic = Image.open(file)
                        pic.thumbnail((1190 if x > 20 else 190, 850))
                        canvas.paste(pic, (x, y))
                canvas.save(frames / f"frame-{len(list(frames.glob('frame-*.png'))):04d}.png")
                workspace.wait_for_timeout(180)

        workspace.get_by_role("button", name="Return to desktop", exact=False).click()
        record(2, "Companion")
        companion.get_by_role("button", name="Open OSCAR Workspace", exact=True).click()
        record(3, "Workspace opened")
        workspace.get_by_role("button", name="Return to desktop", exact=False).click()
        record(2, "Workspace closed; Companion remains")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-framerate",
                "5",
                "-i",
                str(frames / "frame-%04d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(OUTPUT / "companion-workspace.mp4"),
            ],
            check=True,
        )
        companion.get_by_role("button", name="Open OSCAR Workspace", exact=True).click()
        kernel = ctypes.WinDLL("kernel32")
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        process = kernel.OpenProcess(0x00100000, False, info["pid"])
        assert process, "Owned process handle unavailable"
        try:
            workspace.get_by_role("navigation", name="Workspace").get_by_role(
                "button", name="Preferences", exact=True
            ).click()
            workspace.get_by_role("button", name="Quit OSCAR", exact=True).click()
            check(
                "explicit Quit terminates both windows and tray process",
                kernel.WaitForSingleObject(process, 5000) == 0,
            )
        finally:
            kernel.CloseHandle(process)
        released = user.RegisterHotKey(None, 24132, 0x4003, 0x4F)
        try:
            check("explicit Quit releases global shortcut", bool(released))
        finally:
            if released:
                user.UnregisterHotKey(None, 24132)
        result = {
            "evidence": "ACTUAL_TAURI_WEBVIEW2_AUTHENTICATED_DISPOSABLE_CORE",
            "checks": checks,
            "captures": "owned native HWND PrintWindow",
            "recording": "continuous owned HWND captures, side by side, encoded at five fps",
            "model": "SCRIPTED_REFERENCE / no real inference",
            "native_signing": "separate desktop_tauri --self-check",
            "owner_visual_acceptance": "NOT_RUN",
            "physical_voice": "NOT_RUN",
            "native_executable_sha256": hashlib.sha256(
                (ROOT / "desktop/src-tauri/target/debug/oscar-desktop.exe").read_bytes()
            ).hexdigest(),
            "canonical_orb_git_blob": "cb38546cf40c585e1ea5a1f3000832ca10c92ba5",
        }
        (OUTPUT / "acceptance.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result), flush=True)
        try:
            browser.close()
        except Exception:
            pass  # Owned browser process exited through the tested native Quit.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
