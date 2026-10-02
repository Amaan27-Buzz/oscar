"""Provider manifests map official APIs into the same native Grid capability contracts."""

import json
from pathlib import Path
from typing import Any, Protocol

from .connectors import (
    AuthType,
    ConnectorCapability,
    ConnectorError,
    ConnectorManifest,
    RiskLevel,
)


def load_google(path: Path) -> tuple[ConnectorManifest, ...]:
    data = json.loads(path.read_text())
    if set(data) != {"version", "services"} or data["version"] != 1:
        raise ValueError("unsupported Google connector manifest")
    manifests = []
    for family, service in data["services"].items():
        capabilities = tuple(
            ConnectorCapability(
                **{
                    **c,
                    "scopes": tuple(c["scopes"]),
                    "risk": RiskLevel(c["risk"]),
                    "query_fields": tuple(c["query_fields"]),
                }
            )
            for c in service["capabilities"]
        )
        manifests.append(
            ConnectorManifest(
                "google." + family,
                "Google " + family,
                service["origin"],
                capabilities,
                events=("polling", "incremental-sync")
                if family in {"gmail", "calendar"}
                else ("polling",),
                provenance=(
                    "official Google Discovery retrieved 2026-10-03 IST; CONNECTOR-FABRIC.md"
                ),
            )
        )
    return tuple(manifests)


def _cap(
    name: str,
    path: str,
    scopes: tuple[str, ...] = (),
    *,
    method: str = "GET",
    risk: RiskLevel = RiskLevel.READ,
    query: tuple[str, ...] = (),
    body: bool = False,
    read_request: bool = False,
) -> ConnectorCapability:
    return ConnectorCapability(
        name, method, path, scopes, risk, query, body, read_request=read_request
    )


def github_manifest(*, public: bool = False) -> ConnectorManifest:
    # Public read-only mode deliberately excludes private-account and mutation claims.
    reads = (
        _cap("github.repositories.get", "/repos/{owner}/{repo}"),
        _cap(
            "github.issues.list",
            "/repos/{owner}/{repo}/issues",
            query=("state", "per_page", "page"),
        ),
        _cap("github.issues.get", "/repos/{owner}/{repo}/issues/{issue_number}"),
        _cap(
            "github.pulls.list", "/repos/{owner}/{repo}/pulls", query=("state", "per_page", "page")
        ),
        _cap(
            "github.commits.list",
            "/repos/{owner}/{repo}/commits",
            query=("sha", "per_page", "page"),
        ),
        _cap(
            "github.actions.runs",
            "/repos/{owner}/{repo}/actions/runs",
            query=("status", "per_page", "page"),
        ),
        _cap("github.commits.status", "/repos/{owner}/{repo}/commits/{ref}/status"),
    )
    # GitHub list APIs return arrays: adapter normalizes these to {items: [...]}.
    return ConnectorManifest(
        "github.public" if public else "github",
        "GitHub",
        "https://api.github.com",
        reads
        if public
        else reads
        + (
            _cap(
                "github.issues.create",
                "/repos/{owner}/{repo}/issues",
                method="POST",
                risk=RiskLevel.WRITE,
                body=True,
            ),
        ),
        AuthType.NONE if public else AuthType.SESSION,
        headers=(("X-GitHub-Api-Version", "2022-11-28"), ("User-Agent", "OSCAR-reference")),
        provenance="https://docs.github.com/en/rest; retrieved 2026-10-03 IST",
    )


def microsoft_manifest() -> ConnectorManifest:
    return ConnectorManifest(
        "microsoft.graph",
        "Microsoft 365",
        "https://graph.microsoft.com",
        (
            _cap(
                "microsoft.mail.list",
                "/v1.0/me/messages",
                ("Mail.Read",),
                query=("$top", "$filter", "$select", "$skip"),
            ),
            _cap("microsoft.mail.read", "/v1.0/me/messages/{id}", ("Mail.Read",)),
            _cap(
                "microsoft.mail.send",
                "/v1.0/me/sendMail",
                ("Mail.Send",),
                method="POST",
                risk=RiskLevel.COMMUNICATION,
                body=True,
            ),
            _cap(
                "microsoft.calendar.events.list",
                "/v1.0/me/events",
                ("Calendars.Read",),
                query=("$top", "$filter", "$select"),
            ),
            _cap(
                "microsoft.calendar.events.create",
                "/v1.0/me/events",
                ("Calendars.ReadWrite",),
                method="POST",
                risk=RiskLevel.WRITE,
                body=True,
            ),
            _cap(
                "microsoft.onedrive.list",
                "/v1.0/me/drive/root/children",
                ("Files.Read",),
                query=("$top", "$select"),
            ),
            _cap("microsoft.onedrive.metadata", "/v1.0/me/drive/items/{id}", ("Files.Read",)),
            _cap("microsoft.teams.joined", "/v1.0/me/joinedTeams", ("Team.ReadBasic.All",)),
            _cap(
                "microsoft.sharepoint.search", "/v1.0/sites", ("Sites.Read.All",), query=("search",)
            ),
        ),
        provenance="https://learn.microsoft.com/en-us/graph/api/overview; 2026-10-03 IST",
    )


def slack_manifest() -> ConnectorManifest:
    return ConnectorManifest(
        "slack",
        "Slack",
        "https://slack.com",
        (
            _cap(
                "slack.channels.list",
                "/api/conversations.list",
                ("channels:read",),
                query=("cursor", "limit", "types"),
            ),
            _cap(
                "slack.messages.read",
                "/api/conversations.history",
                ("channels:history",),
                query=("channel", "cursor", "limit", "oldest", "latest"),
            ),
            _cap(
                "slack.search",
                "/api/search.messages",
                ("search:read",),
                query=("query", "count", "page"),
            ),
            _cap(
                "slack.messages.post",
                "/api/chat.postMessage",
                ("chat:write",),
                method="POST",
                risk=RiskLevel.COMMUNICATION,
                body=True,
            ),
        ),
        AuthType.SESSION,
        events=("polling", "webhook"),
        provenance="https://docs.slack.dev/reference/methods; 2026-10-03 IST",
    )


def notion_manifest() -> ConnectorManifest:
    return ConnectorManifest(
        "notion",
        "Notion",
        "https://api.notion.com",
        (
            _cap("notion.search", "/v1/search", method="POST", body=True),
            _cap("notion.pages.read", "/v1/pages/{page_id}"),
            _cap(
                "notion.blocks.read",
                "/v1/blocks/{block_id}/children",
                query=("start_cursor", "page_size"),
            ),
            _cap("notion.databases.read", "/v1/databases/{database_id}"),
            _cap("notion.data_sources.read", "/v1/data_sources/{data_source_id}"),
            _cap(
                "notion.data_sources.query",
                "/v1/data_sources/{data_source_id}/query",
                method="POST",
                body=True,
            ),
            _cap(
                "notion.pages.create", "/v1/pages", method="POST", risk=RiskLevel.WRITE, body=True
            ),
            _cap(
                "notion.pages.update",
                "/v1/pages/{page_id}",
                method="PATCH",
                risk=RiskLevel.WRITE,
                body=True,
            ),
        ),
        AuthType.SESSION,
        headers=(("Notion-Version", "2026-03-11"),),
        provenance="https://developers.notion.com/reference/versioning; 2026-10-03 IST",
    )


class MCPSession(Protocol):
    """An authenticated SDK/platform session, not a home-grown MCP transport."""

    def list_tools(self) -> list[dict[str, Any]]: ...
    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


class MCPBoundary:
    """Untrusted tool annotations cannot grant authority or assert successful verification."""

    def __init__(self, session: MCPSession, reviewed: dict[str, RiskLevel]):
        self.session, self.reviewed = session, reviewed

    def manifest(self) -> ConnectorManifest:
        tools = self.session.list_tools()
        if len(tools) > 200:
            raise ConnectorError("tool_manifest_bound")
        caps = []
        for tool in tools:
            name = tool["name"]
            if name not in self.reviewed:
                continue
            if not isinstance(tool.get("inputSchema"), dict):
                raise ConnectorError("invalid_tool_schema")
            caps.append(
                _cap(
                    "mcp." + name,
                    "/tools/{name}",
                    method="POST",
                    risk=self.reviewed[name],
                    body=True,
                    read_request=self.reviewed[name] == RiskLevel.READ,
                )
            )
        return ConnectorManifest(
            "mcp",
            "MCP reviewed session",
            "https://mcp.invalid",
            tuple(caps),
            AuthType.MCP,
            provenance="authenticated external SDK session; owner-reviewed tools",
        )

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self.reviewed:
            raise PermissionError("MCP tool not owner reviewed")
        response = self.session.call_tool(name, arguments)
        if response.get("isError"):
            raise ConnectorError("mcp_tool_failed")
        return response  # Still testimony; only ConnectorVerifier can upgrade an objective.
