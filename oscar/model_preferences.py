"""Shared Core model preferences; callers enforce their surface authority."""

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from .models import Mode

if TYPE_CHECKING:
    from .harness import Harness


def select_model(h: "Harness", value: Any) -> dict[str, Any]:
    from .harness import ModelExecutor

    executor = h.dispatcher.executors.get("models.reason")
    if not isinstance(executor, ModelExecutor):
        raise PermissionError("Model selection unavailable")
    if not isinstance(value, str) or len(value) > 300:
        raise ValueError("Choose an available model")
    candidate = replace(
        executor.template,
        mode=Mode.LOCAL,
        pinned_provider="ollama-local",
        pinned_model=value,
        pinned_slot=None,
    )
    if executor.policy.require_free:
        provider, separator, model = value.partition("::")
        if value and (not separator or not provider or not model):
            raise ValueError("Choose an available cloud model")
        candidate = replace(
            candidate,
            mode=Mode.FREE_FIRST,
            pinned_provider=provider or None,
            pinned_model=model or None,
            ollama_think=None,
        )
    h.router.refresh(candidate, executor.policy)
    if value and not h.router.rank(candidate, executor.policy):
        raise ValueError("Selected model is unavailable under the current routing policy")
    with h.store.transaction():
        h.store.put(
            "desktop_model",
            "selection",
            {
                "configuration": {
                    "mode": candidate.mode.value,
                    "pinned_provider": candidate.pinned_provider,
                    "pinned_model": candidate.pinned_model,
                    "max_output_tokens": candidate.max_output_tokens,
                    "ollama_think": candidate.ollama_think,
                }
            },
        )
        executor.template = candidate
    return {"selected": candidate.pinned_model}


def model_snapshot(h: "Harness") -> dict[str, Any]:
    from .harness import ModelExecutor

    executor = h.dispatcher.executors.get("models.reason")
    template = getattr(executor, "template", None)
    view: dict[str, Any] = {
        "selected": template.pinned_model if template else None,
        "available": sorted(
            {
                m.id
                for (provider, _), inventory in h.registry.inventories.items()
                if provider == "ollama-local" and inventory.source.current(h.grid.clock())
                for m in inventory.models
                if m.active and "text" in m.capabilities
            }
        ),
    }
    if isinstance(executor, ModelExecutor) and template and executor.policy.require_free:
        from dataclasses import replace

        unpinned = replace(template, pinned_provider=None, pinned_model=None)
        view = {
            "selected": (
                template.pinned_provider + "::" + template.pinned_model
                if template.pinned_provider and template.pinned_model
                else ""
            ),
            "available": sorted(
                {
                    route.provider + "::" + route.model
                    for route in h.router.rank(unpinned, executor.policy)
                }
            ),
            "free_only": True,
            "provider_plans": [
                {
                    "id": provider,
                    "confirmed": any(
                        h.router._confirmed_free_plan(s.id)
                        for s in h.pool.slots.values()
                        if s.provider == provider
                    ),
                }
                for provider in ("google", "groq")
                if any(s.provider == provider and s.present for s in h.pool.slots.values())
            ],
        }
    view["available"] = view["available"][:100]
    return view
