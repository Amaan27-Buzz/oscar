"""Shared typed Android task admission; effects run only in the enrolled native app."""

import json
import re
from typing import Any
from urllib.parse import urlsplit

# No arbitrary Intent actions, URI grants, shell, root or system-setting mutation.
ANDROID_CAPABILITIES = {
    "android.app.launch": ("android_app_launch", "android:act", "medium"),
    "android.link.open": ("android_link_open", "android:act", "medium"),
    "android.share.text": ("android_share_text", "android:act", "high"),
    "android.ui.inspect": ("android_ui_inspect", "android:perceive", "low"),
    "android.ui.click": ("android_ui_click", "android:act", "high"),
    "android.ui.set_text": ("android_ui_set_text", "android:act", "high"),
    "android.ui.scroll": ("android_ui_scroll", "android:act", "medium"),
    "android.ui.gesture": ("android_ui_gesture", "android:act", "high"),
    "android.phone.dial": ("android_phone_dial", "android:act", "high"),
    "android.message.compose": ("android_message_compose", "android:act", "high"),
    "android.contact.view": ("android_contact_view", "android:act", "medium"),
    "android.calendar.insert": ("android_calendar_insert", "android:act", "high"),
    "android.settings.open": ("android_settings_open", "android:act", "medium"),
    "android.files.read": ("android_files_read", "android:perceive", "low"),
    "android.files.write": ("android_files_write", "android:act", "high"),
    "android.clipboard.read": ("android_clipboard_read", "android:perceive", "low"),
    "android.clipboard.write": ("android_clipboard_write", "android:act", "high"),
    "android.media.inspect": ("android_media_inspect", "android:perceive", "low"),
    "android.media.control": ("android_media_control", "android:act", "medium"),
    "android.screen.capture": ("android_screen_capture", "android:perceive", "low"),
}


def validate_android(kind: str, parameters: dict[str, Any]) -> dict[str, str]:
    """Exact shape also validated by Kotlin immediately before native dispatch."""
    if kind not in {spec[0] for spec in ANDROID_CAPABILITIES.values()}:
        raise ValueError("unsupported Android capability")
    if set(parameters) != {"package", "target", "value"} or any(
        not isinstance(v, str) for v in parameters.values()
    ):
        raise ValueError("exact Android package, target and value required")
    package, target, value = (parameters[k] for k in ("package", "target", "value"))
    if (
        not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", package)
        or len(package) > 256
        or len(target) > 512
        or len(value) > 2000
        or any("\x00" in v for v in parameters.values())
    ):
        raise ValueError("invalid bounded Android target")
    if kind.startswith("android_ui_"):
        if kind == "android_ui_inspect":
            if target or value:
                raise ValueError("inspection takes no hidden action parameters")
        elif not target.startswith(package + ":id/") or len(target) <= len(package) + 4:
            raise ValueError("exact selected-app resource required")
        if kind == "android_ui_scroll" and value not in {"forward", "backward"}:
            raise ValueError("bounded scroll direction required")
        if kind == "android_ui_gesture" and value not in {"up", "down", "left", "right"}:
            raise ValueError("bounded target-relative gesture required")
        if kind == "android_ui_click" and value:
            raise ValueError("click takes no value")
    elif kind.startswith("android_files_"):
        if (
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,120}\.(?:txt|md|json|csv|log)", target)
            or ".." in target
        ):
            raise ValueError("bounded text document name required")
    elif kind.startswith(("android_clipboard_", "android_media_", "android_screen_")):
        if target:
            raise ValueError("platform operation has no component override")
    elif not target.startswith(package + "."):
        raise ValueError("exact selected Activity component required")
    if (
        kind
        in {
            "android_files_read",
            "android_clipboard_read",
            "android_media_inspect",
            "android_screen_capture",
        }
        and value
    ):
        raise ValueError("read operation takes no mutation value")
    if kind == "android_media_control" and value not in {
        "play",
        "pause",
        "next",
        "previous",
        "stop",
    }:
        raise ValueError("supported media control required")
    if kind == "android_app_launch" and value:
        raise ValueError("launch takes no value")
    if kind == "android_link_open":
        uri = urlsplit(value)
        if uri.scheme != "https" or not uri.hostname or uri.username or uri.password:
            raise ValueError("exact HTTPS app link required")
    if kind == "android_phone_dial" and not re.fullmatch(r"\+?[0-9 ()-]{1,40}", value):
        raise ValueError("bounded telephone number required")
    if kind == "android_message_compose":
        body = json.loads(value)
        if (
            not isinstance(body, dict)
            or set(body) != {"number", "text"}
            or not all(isinstance(v, str) for v in body.values())
            or not re.fullmatch(r"\+?[0-9 ()-]{1,40}", body["number"])
            or len(body["text"]) > 1000
        ):
            raise ValueError("bounded message draft required")
    if kind == "android_contact_view" and not re.fullmatch(r"[0-9]{1,20}", value):
        raise ValueError("exact contact ID required")
    if kind == "android_calendar_insert":
        body = json.loads(value)
        if (
            not isinstance(body, dict)
            or set(body) != {"title", "begin_ms", "end_ms"}
            or not isinstance(body["title"], str)
            or not 0 < len(body["title"]) <= 300
            or type(body["begin_ms"]) is not int
            or type(body["end_ms"]) is not int
            or not 0 < body["begin_ms"] < body["end_ms"] < 4_102_444_800_000
        ):
            raise ValueError("bounded calendar draft required")
    if kind == "android_settings_open" and value not in {
        "wifi",
        "bluetooth",
        "sound",
        "display",
        "application",
    }:
        raise ValueError("supported settings page required")
    return dict(parameters)


def android_readback(parameters: dict[str, Any]) -> dict[str, str]:
    """Readback observes resulting selected-app UI, never repeats the mutation."""
    return {
        "package": parameters["package"],
        "target": parameters["target"]
        if not parameters["target"].startswith(parameters["package"] + ".")
        and ":id/" not in parameters["target"]
        else "",
        "value": "",
    }


def platform_readback_matches(
    operation: str, parameters: dict[str, Any], observed: dict[str, Any]
) -> bool | None:
    """Compare only independent native read results for effects with exact outcomes."""
    if operation not in {"android_files_write", "android_clipboard_write", "android_media_control"}:
        return None
    resource = parameters["target"] or (
        "android.clipboard.read"
        if operation == "android_clipboard_write"
        else "android.media.inspect"
    )
    nodes = observed.get("observations")
    if not isinstance(nodes, list) or len(nodes) != 1 or not isinstance(nodes[0], dict):
        return False
    if observed.get("package") != parameters["package"] or nodes[0].get("resource_id") != resource:
        return False
    if operation != "android_media_control":
        return bool(nodes[0].get("text") == parameters["value"])
    expected = {"play": 3, "pause": 2, "stop": 1}.get(parameters["value"])
    if expected is None:
        return None
    try:
        playback = json.loads(nodes[0]["text"])
        return bool(
            isinstance(playback, dict)
            and playback.get("package") == parameters["package"]
            and type(playback.get("state")) is int
            and playback["state"] == expected
        )
    except (KeyError, TypeError, ValueError):
        return False


def conversation_android(text: str) -> tuple[str | None, str, dict[str, str]] | None:
    """Exact owner-supplied targets only; names, app identity and arguments are never inferred."""
    request = re.sub(
        r"^(?:please |(?:can|could|would) you )", "", text.lstrip(), count=1, flags=re.IGNORECASE
    )
    device = re.fullmatch(
        r"on device ([A-Za-z0-9_.-]{1,80}):\s*(.+)", request, re.IGNORECASE | re.DOTALL
    )
    node, instruction = (device[1], device[2]) if device else (None, request)
    for pattern, kind, fields in (
        (r"read clipboard in (\S+)", "android_clipboard_read", ("package",)),
        (r"copy (.+) to clipboard in (\S+)", "android_clipboard_write", ("value", "package")),
        (
            r"(play|pause|next|previous|stop) media in (\S+)",
            "android_media_control",
            ("value", "package"),
        ),
        (r"inspect media in (\S+)", "android_media_inspect", ("package",)),
        (r"inspect app (\S+)", "android_ui_inspect", ("package",)),
        (r"capture screen of (\S+)", "android_screen_capture", ("package",)),
        (r"read phone file (\S+) in (\S+)", "android_files_read", ("target", "package")),
        (
            r"write phone file (\S+) in (\S+) with text (.+)",
            "android_files_write",
            ("target", "package", "value"),
        ),
        (r"type (.+) into (\S+:id/\S+)", "android_ui_set_text", ("value", "target")),
        (r"click (\S+:id/\S+)", "android_ui_click", ("target",)),
        (r"scroll (\S+:id/\S+) (forward|backward)", "android_ui_scroll", ("target", "value")),
        (r"swipe (\S+:id/\S+) (up|down|left|right)", "android_ui_gesture", ("target", "value")),
        (r"open app (\S+) component (\S+)", "android_app_launch", ("package", "target")),
    ):
        match = re.fullmatch(pattern, instruction, re.IGNORECASE | re.DOTALL)
        if match is None:
            continue
        parameters = {"package": "", "target": "", "value": ""}
        parameters.update(zip(fields, match.groups(), strict=True))
        if not parameters["package"]:
            parameters["package"] = parameters["target"].split(":id/", 1)[0]
        if kind in {"android_media_control", "android_ui_scroll", "android_ui_gesture"}:
            parameters["value"] = parameters["value"].lower()
        return node, kind, validate_android(kind, parameters)
    return None
