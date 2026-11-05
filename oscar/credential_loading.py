"""Read the owner's existing configuration into the opaque credential pool.

Compatibility input only: never writes a credential file or changes process env.
New credentials belong in SetupRuntime's OS Vault, not this legacy input.
"""

import os
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from .models import ProviderSpec

if TYPE_CHECKING:
    from .setup_runtime import SetupRuntime


def existing_provider_environment(path: Path, providers: Iterable[ProviderSpec]) -> dict[str, str]:
    names = {name for provider in providers for name in provider.credential_envs.values()}
    values = {name: os.environ[name] for name in names if os.environ.get(name)}
    if not path.exists():
        return values
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 131072:
        raise ValueError("Existing provider configuration must be a bounded regular file")
    try:
        from dotenv import dotenv_values
    except ImportError:
        raise RuntimeError(
            "Install OSCAR's desktop extra to read existing provider configuration"
        ) from None
    try:
        parsed = dotenv_values(path, interpolate=False, encoding="utf-8-sig")
        for name in names:
            value = parsed.get(name)
            if name not in values and isinstance(value, str) and value and len(value) <= 4096:
                values[name] = value
    except (OSError, ValueError, UnicodeError):
        raise ValueError("Existing provider configuration could not be loaded") from None
    return values


def import_missing_vault_bindings(
    setup: "SetupRuntime", providers: Iterable[ProviderSpec], values: dict[str, str]
) -> None:
    """One-way secure import. Existing and revoked bindings are never overwritten."""
    bound = {
        row["slot"]
        for row in setup.store.all("setup_provider")
        if row["relationship"] == setup.relationship
    }
    for provider in providers:
        for slot, name in provider.credential_envs.items():
            if slot not in bound and values.get(name):
                setup.provider(slot, values[name], owner_authorized=True)
