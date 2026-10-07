"""Independent desktop readback; Worker/API success alone remains REPORTED."""

import subprocess
from time import monotonic, sleep
from typing import Any

from .capabilities import Verifier
from .contracts import Epistemic, Evidence, Objective, Result, TaskState, Verification, new_id
from .windows_desktop import WindowsDesktop


def compare_text(desktop: WindowsDesktop, request: dict[str, Any], expected: str) -> bool | None:
    """Some providers publish ValuePattern updates asynchronously. Retry reads, never writes."""
    deadline = monotonic() + 8
    while monotonic() < deadline:
        try:
            observed = desktop.observe(request, timeout=min(3, deadline - monotonic()))
        except (OSError, ValueError, PermissionError, KeyError, subprocess.SubprocessError):
            return None
        if observed["text"] == expected:
            return True
        sleep(0.05)
    return False


class DesktopVerifier(Verifier):
    def __init__(self, delegate: Verifier, desktop: WindowsDesktop):
        self.delegate, self.desktop = delegate, desktop
        super().__init__(delegate.files, delegate.clock)

    def bind_task(self, task_id: str, parameters: dict[str, Any]) -> None:
        self.delegate.bind_task(task_id, parameters)

    def release_task(self, task_id: str) -> None:
        self.delegate.release_task(task_id)

    def verify(self, objective: Objective, result: Result) -> Verification:
        criterion = objective.criterion
        if criterion["kind"] not in {"desktop_text", "desktop_clipboard"}:
            return self.delegate.verify(objective, result)
        request = criterion.get("request", {"operation": "clipboard_read"})
        matches = compare_text(self.desktop, request, criterion["text"])
        state = (
            TaskState.UNKNOWN
            if matches is None
            else (TaskState.VERIFIED if matches else TaskState.FAILED)
        )
        return Verification(
            state,
            Evidence(
                new_id(),
                result.task_id,
                result.correlation_id,
                "desktop-independent-observer",
                "UIA/clipboard read-after-write exact comparison",
                self.clock(),
                matches,
                Epistemic.VERIFIED if matches else Epistemic.UNKNOWN,
                "destination compared" if matches is not None else "readback unavailable; inspect",
            ),
        )
