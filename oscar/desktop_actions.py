"""Bounded owner forms translated to existing Worker contracts at the authoritative Core."""

import hashlib
import re
from pathlib import Path
from typing import Any

from .browser_worker import origin
from .contracts import Capability
from .jev import Intent
from .windows_files import WindowsScopedFiles

OPERATIONS = {
    "file_write": ("write_file",),
    "file_read": ("read_file",),
    "directory_list": ("list_files",),
    "file_search": ("find_files",),
    "git_operation": ("git_status", "git_diff", "git_log", "git_branches", "git_branch"),
    "powershell": ("ps_environment", "ps_file_hash", "ps_write_utf8"),
    "terminal_command": ("program_version",),
    "browser": ("inspect_page",),
    "installed_app": ("list_apps", "launch_app"),
    "executable_discovery": ("worker_tools",),
}


def conversation_form(text: str) -> tuple[str, dict[str, str]] | None:
    """Only explicit bounded operations; inference never supplies an action's arguments."""
    request = re.sub(
        r"^(?:please |(?:can|could|would) you )", "", text.lstrip(), count=1, flags=re.IGNORECASE
    )
    for pattern, operation, fields in (
        (
            r'(?:write|create)(?: a)?(?: file)? ["\']?([^\s"\']+)["\']? '
            r"(?:with(?: content| text)?|containing)\s+(.+)",
            "write_file",
            ("path", "text"),
        ),
        (r'(?:read|show)(?: the)? file ["\']?([^\s"\']+)["\']?', "read_file", ("path",)),
        (r"(?:list|show)(?: the)? files", "list_files", ()),
        (r"find files (?:matching )?(.+)", "find_files", ("pattern",)),
        (r"(?:check|show)(?: the)? git status", "git_status", ()),
        (r"(?:show|check)(?: the)? git diff", "git_diff", ()),
        (r"(?:create|make)(?: a)? branch (\S+)", "git_branch", ("name",)),
        (r"(?:inspect|read)(?: the)? page (https?://\S+)", "inspect_page", ("url",)),
    ):
        match = re.fullmatch(
            pattern,
            request if operation == "write_file" else request.strip(),
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return operation, dict(zip(fields, match.groups(), strict=True))
    return None


def editing_request(text: str) -> bool:
    request = re.sub(
        r"^(?:please |(?:can|could|would) you )", "", text.strip(), count=1, flags=re.IGNORECASE
    )
    return bool(
        re.match(
            r"(?:edit|rewrite|rephrase|shorten|polish|translate)\b|fix\b.*\b(?:grammar|spelling)\b"
            r"|make (?:this|the selected text|the selection) (?:shorter|clearer|more concise)\b",
            request,
            re.IGNORECASE,
        )
    )


def programs(native: dict[str, Any]) -> dict[str, str]:
    return {
        hashlib.sha256(p.encode()).hexdigest()[:24]: p
        for p in native.get("executables", ())
        if Path(p).name.lower() in {"python.exe", "python", "python3", "git.exe", "git", "pwsh.exe"}
    }


def public_capability(cap: Capability, native: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": cap.node_id + "::" + cap.id,
        "node": cap.node_id,
        "kind": cap.input_kind,
        "label": cap.name,
        "summary": cap.summary[:200],
        "risk": cap.risk,
        "permissions": list(cap.permissions),
        "operations": list(OPERATIONS.get(cap.input_kind, ())),
        "programs": [{"id": k, "name": Path(v).name} for k, v in programs(native).items()],
        "applications": [
            {"id": a["id"], "name": a["name"]}
            for a in native.get("applications", ())
            if a.get("launch_authorized")
        ],
    }


def form_intent(cap: Capability, payload: dict[str, Any], native: dict[str, Any]) -> Intent:
    if set(payload) != {"capability_id", "operation", "fields"} or not isinstance(
        payload["fields"], dict
    ):
        raise ValueError("typed Act form required")
    operation, fields = payload["operation"], payload["fields"]
    if operation not in OPERATIONS.get(cap.input_kind, ()):
        raise PermissionError("operation is not advertised by this capability")
    allowed_fields = {
        "write_file": {"path", "text"},
        "read_file": {"path"},
        "list_files": set(),
        "find_files": {"pattern"},
        "git_status": set(),
        "git_diff": set(),
        "git_log": set(),
        "git_branches": set(),
        "git_branch": {"name"},
        "ps_environment": set(),
        "ps_file_hash": {"path"},
        "ps_write_utf8": {"path", "text"},
        "program_version": {"program_id"},
        "inspect_page": {"url"},
        "list_apps": set(),
        "launch_app": {"app_id"},
        "worker_tools": set(),
    }
    if set(fields) != allowed_fields[operation] or any(
        not isinstance(v, str) or len(v) > (4096 if k == "text" else 500) for k, v in fields.items()
    ):
        raise ValueError("invalid bounded Act fields")
    if "path" in fields:
        WindowsScopedFiles.parts(fields["path"])
    parameters: dict[str, Any]
    criterion: dict[str, Any] = {"kind": "unavailable"}
    if operation == "write_file":
        parameters = {"path": fields["path"], "content": fields["text"]}
        criterion = {"kind": "file_exact", **parameters}
    elif operation == "read_file":
        parameters = {"path": fields["path"]}
    elif operation in {"list_files", "find_files"}:
        parameters = {"cwd": "."}
        if operation == "find_files":
            parameters["pattern"] = fields["pattern"]
    elif operation.startswith("git_"):
        parameters = {"operation": operation.removeprefix("git_"), **fields}
    elif operation.startswith("ps_"):
        request = {"operation": operation.removeprefix("ps_"), **fields}
        if operation == "ps_write_utf8":
            request["content"] = request.pop("text")
            criterion = {"kind": "file_exact", "path": fields["path"], "content": fields["text"]}
        parameters = {"request": request, "timeout": 15}
    elif operation == "program_version":
        executable = programs(native).get(fields["program_id"])
        if executable is None:
            raise PermissionError("registered version executor unavailable")
        parameters = {"argv": [executable, "--version"], "timeout": 10, "cwd": "."}
    elif operation == "inspect_page":
        url = fields["url"]
        parameters = {
            "request": {
                "origins": [origin(url)],
                "steps": [{"operation": "navigate", "url": url}, {"operation": "inspect"}],
                "timeout": 15,
                "max_text": 4096,
            }
        }
    elif operation == "list_apps":
        parameters = {"request": {"operation": "catalog"}}
    elif operation == "launch_app":
        if fields["app_id"] not in {
            a["id"] for a in native.get("applications", ()) if a.get("launch_authorized")
        }:
            raise PermissionError("registered application required")
        parameters = {"request": {"operation": "launch", "app_id": fields["app_id"]}}
    else:
        parameters = {}
    return Intent(
        "Desktop owner " + operation,
        kind="capability",
        capability_kind=cap.input_kind,
        parameters=parameters,
        criterion=criterion,
    )
