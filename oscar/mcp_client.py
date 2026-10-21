"""Official MCP SDK sessions, reviewed installations and Connector Fabric projection.

Local servers execute trusted code with the user's OS rights; this is not a sandbox.
Only explicit connect launches a process, including after Core restart.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import ipaddress
import json
import os
import re
import socket
import threading
from collections.abc import Callable
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from time import monotonic, time
from typing import Any
from urllib.parse import urlsplit

from .capabilities import Cancellation, Cancelled
from .connector_providers import MCPBoundary, MCPConnectorHTTP
from .connectors import (
    ConnectionState,
    ConnectorCapability,
    ConnectorError,
    ConnectorFabric,
    ConnectorInstance,
    ConnectorManifest,
    CredentialRef,
    RiskLevel,
)
from .credentials import redact_runtime_secrets
from .storage import Store


def schema_digest(schema: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(schema, sort_keys=True, allow_nan=False).encode()).hexdigest()


def executable_digest(path: str) -> str:
    target = Path(path)
    if not target.is_absolute() or not target.is_file() or target.is_symlink():
        raise ValueError("MCP executable/reviewed file must be an absolute regular file")
    return hashlib.sha256(target.read_bytes()).hexdigest()


def validate_schema(schema: Any) -> None:
    from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

    if not isinstance(schema, dict) or len(json.dumps(schema)) > 100000:
        raise ConnectorError("invalid_tool_schema")

    def check_refs(value: Any, depth: int = 0) -> None:
        if depth > 30:
            raise ConnectorError("tool_schema_depth_bound")
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"$ref", "$dynamicRef", "$recursiveRef"} and (
                    not isinstance(child, str) or not child.startswith("#")
                ):
                    raise ConnectorError("external_schema_reference")
                check_refs(child, depth + 1)
        elif isinstance(value, list):
            for child in value:
                check_refs(child, depth + 1)

    check_refs(schema)
    Draft202012Validator.check_schema(schema)


def validate_destination(url: str, fixture_origin: str | None = None) -> tuple[str, str]:
    """Resolve once and pin a public destination; fixture exception is exact loopback origin."""
    if any(ord(c) < 33 for c in url) or len(url) > 2048:
        raise ValueError("invalid MCP destination")
    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("MCP destination cannot carry credentials/query/fragment")
    origin = f"{parsed.scheme}://{parsed.netloc}"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = sorted(
        {str(r[4][0]) for r in socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)}
    )
    approved_fixture = fixture_origin == origin and all(
        ipaddress.ip_address(a).is_loopback for a in addresses
    )
    if not addresses or (
        not approved_fixture
        and (
            parsed.scheme != "https"
            or any(not ipaddress.ip_address(a).is_global for a in addresses)
        )
    ):
        raise ValueError("MCP destination must be public HTTPS or exact approved loopback fixture")
    return origin, addresses[0]


@dataclass(frozen=True)
class MCPServerConfig:
    id: str
    name: str
    account_id: str
    account_generation: int = 1
    command: str | None = None
    arguments: tuple[str, ...] = ()
    cwd: str | None = None
    url: str | None = None
    credential_ref: str | None = None
    fixture_origin: str | None = None
    timeout: float = 15
    # Hash executable AND scripts/config supplied as executable arguments at review time.
    reviewed_files: tuple[tuple[str, str], ...] = ()
    read_resources: bool = False
    get_prompts: bool = False

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", self.id):
            raise ValueError("invalid MCP installation id")
        if not self.name or len(self.name) > 120 or not self.account_id:
            raise ValueError("MCP name and account binding required")
        if type(self.account_generation) is not int or self.account_generation < 1:
            raise ValueError("invalid MCP account generation")
        if bool(self.command) == bool(self.url) or not 0 < self.timeout <= 60:
            raise ValueError("choose stdio OR HTTP and a bounded timeout")
        if len(self.arguments) > 32 or len(json.dumps(asdict(self))) > 16000:
            raise ValueError("MCP launch configuration bound exceeded")
        if self.command and (not Path(self.command).is_absolute() or not self.reviewed_files):
            raise ValueError("stdio requires reviewed executable identity")
        if self.cwd and not Path(self.cwd).is_absolute():
            raise ValueError("MCP cwd must be absolute")
        if self.command and self.credential_ref:
            raise ValueError("stdio credential delivery requires a separately reviewed adapter")
        if redact_runtime_secrets(json.dumps(asdict(self))) != json.dumps(asdict(self)):
            raise ValueError("MCP configuration cannot contain secret material")


class MCPClient:
    """Synchronous Fabric bridge; one thread owns SDK context entry and teardown."""

    def __init__(
        self,
        config: MCPServerConfig,
        authorize: Callable[[], None],
        secret: Callable[[], str | None],
    ):
        self.config, self.authorize, self.secret = config, authorize, secret
        self.tools: list[dict[str, Any]] = []
        self.schemas: dict[str, str] = {}
        self.metadata: dict[str, Any] = {}
        self._ready = threading.Event()
        self._transport_closed = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop: asyncio.Event | None = None
        self._client: Any = None
        self._context = threading.local()
        self._error: BaseException | None = None
        self._thread = threading.Thread(
            target=self._run, name="oscar-mcp-" + config.id, daemon=True
        )
        self._thread.start()
        if not self._ready.wait(config.timeout + 2):
            self.close()
            raise ConnectorError("mcp_connection_timeout")
        if self._error:
            raise ConnectorError("mcp_connection_failed") from None

    @asynccontextmanager
    async def _transport(self) -> Any:
        from mcp.client.stdio import StdioServerParameters, get_default_environment, stdio_client
        from mcp.client.streamable_http import streamable_http_client

        config = self.config
        self.authorize()
        if config.command:
            reviewed = dict(config.reviewed_files)
            if config.command not in reviewed:
                raise PermissionError("MCP executable was not reviewed")
            for path, digest in reviewed.items():
                if executable_digest(path) != digest:
                    raise PermissionError("MCP executable identity changed; review required")
            # Override SDK inheritance, including PATH and home directories; no provider secrets.
            env = dict.fromkeys(get_default_environment(), "")
            env.update(
                {
                    k: os.environ[k]
                    for k in ("SYSTEMROOT", "SYSTEMDRIVE", "TEMP", "TMP")
                    if k in os.environ
                }
            )
            env["PATH"] = str(Path(config.command).parent)
            params = StdioServerParameters(
                command=config.command, args=list(config.arguments), cwd=config.cwd, env=env
            )
            with open(os.devnull, "w") as errlog:
                async with stdio_client(params, errlog=errlog) as streams:
                    yield self._observed_streams(streams)
        else:
            import httpx2

            assert config.url is not None
            origin, address = validate_destination(config.url, config.fixture_origin)
            original = urlsplit(config.url)

            class PinnedTransport(httpx2.AsyncBaseTransport):
                def __init__(self) -> None:
                    self.inner = httpx2.AsyncHTTPTransport(trust_env=False, retries=0)

                async def handle_async_request(self, request: Any) -> Any:
                    if str(request.url).split("?", 1)[0] != config.url:
                        raise PermissionError("MCP request changed reviewed destination")
                    if request.headers.get("origin") not in {None, origin}:
                        raise PermissionError("MCP request origin mismatch")
                    request.headers["host"] = original.netloc
                    request.extensions["sni_hostname"] = original.hostname
                    request.url = request.url.copy_with(host=address)
                    return await self.inner.handle_async_request(request)

                async def aclose(self) -> None:
                    await self.inner.aclose()

            token = self.secret()
            if token and ("\r" in token or "\n" in token):
                raise ValueError("invalid MCP credential")
            headers = {"Origin": origin}
            if token:
                headers["Authorization"] = "Bearer " + token
            async with httpx2.AsyncClient(
                transport=PinnedTransport(),
                headers=headers,
                trust_env=False,
                follow_redirects=False,
                timeout=httpx2.Timeout(config.timeout),
            ) as http:
                async with streamable_http_client(config.url, http_client=http) as streams:
                    yield self._observed_streams(streams)

    def _observed_streams(self, streams: Any) -> Any:
        owner = self
        read, write = streams

        class ObservedReceive:
            async def __aenter__(self) -> Any:
                await read.__aenter__()
                return self

            async def __aexit__(self, *args: Any) -> Any:
                return await read.__aexit__(*args)

            def __aiter__(self) -> Any:
                return self

            async def __anext__(self) -> Any:
                try:
                    return await read.__anext__()
                except StopAsyncIteration:
                    owner._transport_closed.set()
                    if owner._stop:
                        owner._stop.set()
                    raise

        return ObservedReceive(), write

    def _run(self) -> None:
        try:
            asyncio.run(self._serve())
        except BaseException as error:
            self._error = error
        finally:
            self._ready.set()

    async def _serve(self) -> None:
        from mcp import Client

        self._loop = asyncio.get_running_loop()
        self._stop = asyncio.Event()
        async with AsyncExitStack() as stack:
            self._client = await stack.enter_async_context(
                Client(
                    self._transport(),
                    read_timeout_seconds=self.config.timeout,
                    cache=None,
                    message_handler=self._notification,
                )
            )
            info = self._client.server_info
            self.metadata = {
                "protocol_version": self._client.protocol_version,
                "server_info": info.model_dump(by_alias=True) if info else None,
                "server_capabilities": self._client.server_capabilities.model_dump(by_alias=True),
                "notifications": 0,
            }
            if len(json.dumps(self.metadata)) > 16000:
                raise ConnectorError("mcp_metadata_bound")
            await self._refresh()
            self._ready.set()
            await self._stop.wait()

    async def _notification(self, message: Any) -> None:
        # Discovery is refreshed before every call, also covering modern subscription invalidations.
        self.metadata["notifications"] = self.metadata.get("notifications", 0) + 1

    async def _refresh(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        cursor = None
        for _ in range(20):
            result = await self._client.list_tools(cursor=cursor)
            tools.extend(t.model_dump(by_alias=True, exclude_none=True) for t in result.tools)
            if len(tools) > 200:
                raise ConnectorError("tool_manifest_bound")
            cursor = result.next_cursor
            if cursor is None:
                break
        else:
            raise ConnectorError("tool_manifest_pagination_bound")
        names = set()
        if len(json.dumps(tools)) > 100000:
            raise ConnectorError("tool_manifest_bound")
        for tool in tools:
            name = tool["name"]
            if (
                name in names
                or name.casefold().startswith("oscar.")
                or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", name)
            ):
                raise ConnectorError("invalid_tool_identity")
            names.add(name)
            schema = tool["inputSchema"]
            if schema.get("type") != "object":
                raise ConnectorError("invalid_tool_schema")
            validate_schema(schema)
            if "outputSchema" in tool:
                validate_schema(tool["outputSchema"])
        if self.config.read_resources:
            tools.append(
                {
                    "name": "oscar.resources.read",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"uri": {"type": "string", "maxLength": 2048}},
                        "required": ["uri"],
                        "additionalProperties": False,
                    },
                }
            )
        if self.config.get_prompts:
            tools.append(
                {
                    "name": "oscar.prompts.get",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "arguments": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                        },
                        "required": ["name"],
                        "additionalProperties": False,
                    },
                }
            )
        self.tools = tools
        return tools

    def _submit(self, operation: str, *arguments: Any) -> Any:
        self.authorize()
        if not self._loop or not self._thread.is_alive() or not self._client:
            raise ConnectorError("mcp_disconnected")
        future = asyncio.run_coroutine_threadsafe(
            self._operation(operation, *arguments), self._loop
        )
        try:
            deadline = monotonic() + self.config.timeout + 1
            while True:
                cancellation = getattr(self._context, "cancellation", None)
                if cancellation:
                    cancellation.check()
                self.authorize()
                try:
                    return future.result(min(0.1, max(0.001, deadline - monotonic())))
                except concurrent.futures.TimeoutError:
                    if future.done() or monotonic() >= deadline:
                        raise ConnectorError("mcp_timeout") from None
        except (PermissionError, ValueError, ConnectorError, Cancelled):
            future.cancel()  # SDK cancels the request; never retry an uncertain mutation.
            raise
        except Exception:
            future.cancel()
            raise ConnectorError("mcp_request_failed") from None

    async def _operation(self, operation: str, *arguments: Any) -> Any:
        from jsonschema import Draft202012Validator

        self.authorize()
        async with asyncio.timeout(self.config.timeout):
            if operation == "tools":
                return await self._refresh()
            if operation == "resources":
                return (await self._client.list_resources()).model_dump(by_alias=True, mode="json")
            if operation == "prompts":
                return (await self._client.list_prompts()).model_dump(by_alias=True, mode="json")
            name, values = arguments
            await self._refresh()
            definition = next((t for t in self.tools if t["name"] == name), None)
            if definition is None:
                raise ConnectorError("mcp_tool_removed")
            digest = schema_digest(definition["inputSchema"])
            if self.schemas.get(name) != digest:
                raise PermissionError("MCP tool schema changed; review required")
            Draft202012Validator(definition["inputSchema"]).validate(values)
            self.authorize()
            if name == "oscar.resources.read":
                response = await self._client.read_resource(values["uri"])
            elif name == "oscar.prompts.get":
                response = await self._client.get_prompt(values["name"], values.get("arguments"))
            else:
                response = await self._client.call_tool(name, values)
            payload = response.model_dump(by_alias=True, mode="json", exclude_none=True)
            if len(json.dumps(payload)) > 2_000_000:
                raise ConnectorError("response_bound")
            return payload

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._submit("tools"))

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return dict(self._submit("call", name, arguments))

    def close(self) -> None:
        if self._loop and self._stop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._stop.set)
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout=self.config.timeout + 5)
        self._client = None


class MCPPlugins:
    """Persist installations in Store and project only live reviewed tools into Fabric/Grid."""

    def __init__(
        self,
        store: Store,
        fabric: ConnectorFabric,
        authorize_account: Callable[[str, int], object] | None = None,
    ):
        self.store, self.fabric, self.authorize_account = store, fabric, authorize_account
        self.sessions: dict[str, MCPClient] = {}
        self.adapters: dict[str, MCPConnectorHTTP] = {}
        self._lifecycle_lock = threading.RLock()
        self._fallback = fabric.http
        fabric.http = self
        store.close_callbacks.append(self.close)

    def register(
        self,
        config: MCPServerConfig,
        reviewed: dict[str, RiskLevel | tuple[RiskLevel, ...]],
        *,
        owner_reviewed: bool = False,
    ) -> None:
        if not owner_reviewed:
            raise PermissionError("MCP installation requires explicit owner review")
        if any(r["id"] == config.id for r in self.store.all("mcp_installation")):
            raise ValueError("MCP installation already exists")
        if len(self.store.all("mcp_installation")) >= 16:
            raise ValueError("MCP installation bound exceeded")
        if config.url:
            validate_destination(config.url, config.fixture_origin)
        for path, digest in config.reviewed_files:
            if executable_digest(path) != digest:
                raise ValueError("MCP executable identity mismatch")
        risks = {
            name: [r.value for r in ((value,) if isinstance(value, RiskLevel) else value)]
            for name, value in reviewed.items()
        }
        if any(not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", name) for name in risks):
            raise ValueError("invalid reviewed MCP tool name")
        if config.read_resources:
            risks["oscar.resources.read"] = [RiskLevel.READ.value]
        if config.get_prompts:
            risks["oscar.prompts.get"] = [RiskLevel.READ.value]
        if not risks or any(not value for value in risks.values()):
            raise ValueError("explicit MCP tool permissions required")
        self.store.put(
            "mcp_installation",
            config.id,
            {
                "id": config.id,
                "config": asdict(config),
                "reviewed": risks,
                "enabled": True,
                "schemas": {},
                "health": "disconnected",
                "activity": [],
            },
        )

    def _config(self, record: dict[str, Any]) -> MCPServerConfig:
        data = dict(record["config"])
        data["arguments"] = tuple(data["arguments"])
        data["reviewed_files"] = tuple(tuple(p) for p in data["reviewed_files"])
        return MCPServerConfig(**data)

    def _authorize(self, identifier: str, config: MCPServerConfig) -> None:
        current = self.store.get("mcp_installation", identifier)
        if not current["enabled"] or current["config"] != asdict(config):
            # SQLite JSON normalizes tuples to lists.
            if not current["enabled"] or self._config(current) != config:
                raise PermissionError("MCP installation disabled or account binding changed")
        if self.authorize_account:
            self.authorize_account(config.account_id, config.account_generation)
        if config.credential_ref:
            accounts = self.fabric.accounts
            if accounts is None or config.url is None:
                raise PermissionError("MCP HTTP credential requires the trusted account registry")
            owner = self.store.get("account_credential_owner", config.credential_ref)
            if owner["account_id"] != config.account_id:
                raise PermissionError("MCP credential belongs to another account")
            accounts.check(
                config.account_id,
                config.account_generation,
                service=owner["service"],
                audience=config.url,
                credential=CredentialRef(config.credential_ref),
            )

    def connect(
        self,
        identifier: str,
        *,
        expected_config: MCPServerConfig | None = None,
    ) -> dict[str, Any]:
        # SDK launch/teardown is serialized so a late failed connect cannot remove a newer session.
        with self._lifecycle_lock:
            return self._connect(identifier, expected_config=expected_config)

    def _connect(
        self,
        identifier: str,
        *,
        expected_config: MCPServerConfig | None = None,
    ) -> dict[str, Any]:
        initial = self._config(self.store.get("mcp_installation", identifier))
        if expected_config is not None and initial != expected_config:
            raise PermissionError("MCP installation changed after review")
        self.disconnect(identifier, expected_config=initial)
        record = self.store.get("mcp_installation", identifier)
        config = self._config(record)
        if config != initial:
            raise PermissionError("MCP installation changed during connect")
        self._authorize(identifier, config)
        reference = CredentialRef(config.credential_ref) if config.credential_ref else None

        def secret() -> str | None:
            if reference is None:
                return None
            value = self.fabric.secrets.resolve(reference)
            if not value:
                raise PermissionError("MCP credential unavailable")
            return value

        try:
            client = MCPClient(config, lambda: self._authorize(identifier, config), secret)
            tools = client.list_tools()
            schemas = {
                t["name"]: schema_digest(t["inputSchema"])
                for t in tools
                if t["name"] in record["reviewed"]
            }
            if record["schemas"] and record["schemas"] != schemas:
                client.close()
                raise PermissionError("MCP tools changed; explicit review required")
            client.schemas = schemas
            reviewed: dict[str, RiskLevel | tuple[RiskLevel, ...]] = {
                n: tuple(RiskLevel(r) for r in risks) for n, risks in record["reviewed"].items()
            }
            boundary = MCPBoundary(client, reviewed, manifest_id="mcp." + identifier)
            manifest = boundary.manifest()
            with self.store.transaction():
                self._authorize(identifier, config)
                record = self.store.get("mcp_installation", identifier)
                self.sessions[identifier] = client
                self.adapters[manifest.id] = MCPConnectorHTTP(boundary)
                self.fabric.install(
                    ConnectorInstance(
                        identifier,
                        manifest,
                        session_ready=True,
                        account_id=config.account_id,
                        account_generation=config.account_generation,
                    )
                )
                record.update(schemas=schemas, health="ready")
                self._save_activity(record, "connected")
            return self.inspect(identifier)
        except Exception:
            if "client" in locals():
                client.close()
            self.sessions.pop(identifier, None)
            self.adapters.pop("mcp." + identifier, None)
            self.fabric.instances.pop(identifier, None)
            # A failed launch must not restore removed or replaced installation metadata.
            with self.store.transaction():
                try:
                    current = self.store.get("mcp_installation", identifier)
                except KeyError:
                    pass
                else:
                    if self._config(current) == config and current["enabled"]:
                        current["health"] = "failed"
                        self._save_activity(current, "connect_failed")
            raise

    def _save_activity(self, record: dict[str, Any], event: str) -> None:
        record["activity"] = [*record["activity"][-19:], {"event": event, "at": time()}]
        self.store.put("mcp_installation", record["id"], record)

    def disconnect(
        self,
        identifier: str,
        *,
        expected_config: MCPServerConfig | None = None,
    ) -> None:
        with self._lifecycle_lock:
            self._disconnect(identifier, expected_config=expected_config)

    def _disconnect(
        self,
        identifier: str,
        *,
        expected_config: MCPServerConfig | None = None,
    ) -> None:
        client = self.sessions.get(identifier)
        if client and expected_config is not None and client.config != expected_config:
            return
        self.sessions.pop(identifier, None)
        self.adapters.pop("mcp." + identifier, None)
        self.fabric.instances.pop(identifier, None)
        if client:
            client.close()
        try:
            record = self.store.get("mcp_installation", identifier)
        except KeyError:
            return
        if expected_config is not None and self._config(record) != expected_config:
            return
        record["health"] = "disconnected"
        self._save_activity(record, "disconnected")

    def set_enabled_local(self, identifier: str, enabled: bool) -> None:
        if not self.store.db.in_transaction or type(enabled) is not bool:
            raise ValueError("MCP local mutation requires the owner-review transaction")
        record = self.store.get("mcp_installation", identifier)
        record.update(enabled=enabled, health="disconnected")
        self._save_activity(record, "enabled" if enabled else "disabled")

    def remove_local(self, identifier: str) -> None:
        if not self.store.db.in_transaction:
            raise ValueError("MCP local removal requires the owner-review transaction")
        self.store.delete("mcp_installation", identifier)

    def enable(self, identifier: str, enabled: bool) -> None:
        if type(enabled) is not bool:
            raise ValueError("MCP enabled must be boolean")
        self.disconnect(identifier)
        record = self.store.get("mcp_installation", identifier)
        record["enabled"] = enabled
        self._save_activity(record, "enabled" if enabled else "disabled")

    def bind_account(self, identifier: str, account_id: str, generation: int) -> None:
        self.disconnect(identifier)
        record = self.store.get("mcp_installation", identifier)
        config = replace(self._config(record), account_id=account_id, account_generation=generation)
        if self.authorize_account:
            self.authorize_account(account_id, generation)
        record["config"] = asdict(config)
        self._save_activity(record, "account_changed")

    def remove(self, identifier: str) -> None:
        self.disconnect(identifier)
        self.store.delete("mcp_installation", identifier)

    def inspect(self, identifier: str) -> dict[str, Any]:
        record = self.store.get("mcp_installation", identifier)
        config = self._config(record)
        client = self.sessions.get(identifier)
        state = self.connection_state(self.fabric.instances.get(identifier))
        snapshot = {
            "id": identifier,
            "name": config.name,
            "account_id": config.account_id,
            "account_generation": config.account_generation,
            "enabled": record["enabled"],
            "transport": "stdio" if config.command else "streamable-http",
            "command": config.command,
            "url": config.url,
            "reviewed_files": config.reviewed_files,
            "health": "ready" if state == ConnectionState.READY else "disconnected",
            "last_health": record["health"],
            "permissions": record["reviewed"],
            "tools": client.tools if client else [],
            "metadata": client.metadata if client else {},
            "activity": record["activity"],
        }
        return dict(json.loads(self.fabric.secrets.redact(json.dumps(snapshot))))

    def connection_state(self, instance: ConnectorInstance | None) -> ConnectionState | None:
        if instance is None or not instance.manifest.id.startswith("mcp."):
            return None
        client = self.sessions.get(instance.id)
        if (
            not client
            or not client._thread.is_alive()
            or client._error
            or client._transport_closed.is_set()
        ):
            return ConnectionState.UNAVAILABLE
        try:
            self._authorize(instance.id, client.config)
        except (KeyError, PermissionError):
            return ConnectionState.AUTH_MISSING
        return ConnectionState.READY

    def snapshot(self) -> list[dict[str, Any]]:
        return [self.inspect(r["id"]) for r in self.store.all("mcp_installation")]

    def discovery(self, identifier: str, kind: str) -> dict[str, Any]:
        if kind not in {"resources", "prompts"}:
            raise ValueError("unknown MCP discovery kind")
        client = self.sessions[identifier]
        if not (client.config.read_resources if kind == "resources" else client.config.get_prompts):
            raise PermissionError("MCP metadata access was not reviewed")
        return dict(client._submit(kind))

    def request(
        self,
        manifest: ConnectorManifest,
        spec: ConnectorCapability,
        parameters: dict[str, Any],
        secret: str | None,
    ) -> tuple[dict[str, Any], str]:
        if not manifest.id.startswith("mcp."):
            return self._fallback.request(manifest, spec, parameters, secret)
        adapter = self.adapters.get(manifest.id)
        if adapter is None:
            raise ConnectorError("mcp_disconnected")
        identifier = manifest.id.removeprefix("mcp.")
        config = self.sessions[identifier].config
        self._authorize(identifier, config)
        try:
            result = adapter.request(manifest, spec, parameters, secret)
        except Exception:
            self._save_activity(self.store.get("mcp_installation", identifier), "tool_failed")
            raise
        self._save_activity(self.store.get("mcp_installation", identifier), "tool_reported")
        return result[0], "mcp://" + identifier + "/" + spec.name.removeprefix("mcp.")

    def request_cancellable(
        self,
        manifest: ConnectorManifest,
        spec: ConnectorCapability,
        parameters: dict[str, Any],
        secret: str | None,
        cancellation: Cancellation,
    ) -> tuple[dict[str, Any], str]:
        if not manifest.id.startswith("mcp."):
            return self._fallback.request(manifest, spec, parameters, secret)
        client = self.sessions.get(manifest.id.removeprefix("mcp."))
        if client is None:
            raise ConnectorError("mcp_disconnected")
        client._context.cancellation = cancellation
        try:
            return self.request(manifest, spec, parameters, secret)
        finally:
            del client._context.cancellation

    def close(self) -> None:
        for identifier in list(self.sessions):
            self.disconnect(identifier)
