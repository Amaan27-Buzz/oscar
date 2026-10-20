"""Real MCP processes in the existing Core Runtime, Grid, Ask and artifact lifecycle."""

import importlib.util
import sys
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from oscar.connectors import RiskLevel
from oscar.harness import Harness
from oscar.jev import Intent
from oscar.mcp_client import MCPServerConfig, executable_digest
from oscar.storage import StateConflict


@unittest.skipUnless(importlib.util.find_spec("mcp"), "install oscar-brain[mcp]")
class ConnectorMountTests(unittest.TestCase):
    def test_existing_runtime_two_accounts_exact_ask_and_verified_artifact(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            with Harness(
                root / "core.sqlite",
                root / "workspace",
                Path("config/development-models.json"),
                start_services=False,
            ) as h:
                original_scopes = h.store.get("node", h.node_id)["scopes"]
                accounts = []
                for identifier, script in (
                    ("knowledge", "mcp_knowledge.py"),
                    ("writer", "mcp_workspace.py"),
                ):
                    account = h.accounts.add(
                        "fixture", "synthetic", identifier, identifier, verified=True
                    )
                    accounts.append(account)
                    command = str(Path(sys.executable).resolve())
                    fixture = str(Path(__file__).parent.resolve() / "fixtures" / script)
                    arguments = (
                        (account.id,)
                        if identifier == "knowledge"
                        else (str(h.files.root), account.id)
                    )
                    h.plugins.register(
                        MCPServerConfig(
                            identifier,
                            identifier,
                            account.id,
                            command=command,
                            arguments=("-I", fixture, *arguments),
                            cwd=str(root),
                            reviewed_files=(
                                (command, executable_digest(command)),
                                (fixture, executable_digest(fixture)),
                            ),
                        ),
                        {"lookup": RiskLevel.READ}
                        if identifier == "knowledge"
                        else {"read_file": RiskLevel.READ, "write_file": RiskLevel.WRITE},
                        owner_reviewed=True,
                    )
                    h.plugins.connect(identifier)
                grants = ("connectors:read", "connectors:write")
                with self.assertRaises(PermissionError):
                    h.mount_connectors("plugins", grants, owner_authorized=False)
                mount = h.mount_connectors("plugins", grants, owner_authorized=True)
                self.assertEqual(original_scopes, h.store.get("node", h.node_id)["scopes"])
                with self.assertRaises(ValueError):
                    mount.capability("mcp.lookup", account_id=accounts[1].id)
                lookup = mount.capability("mcp.lookup", account_id=accounts[0].id)
                responses = []
                original_execute = h.connectors.execute

                def capture(*args, **kwargs):
                    outcome = original_execute(*args, **kwargs)
                    responses.append(outcome)
                    return outcome

                request = h.connectors.stage(
                    {"path": {"name": "lookup"}, "body": {"topic": "research"}}
                )
                task = h.runtime.create(
                    Intent(
                        "Read synthetic research",
                        "capability",
                        capability_kind=lookup.id,
                        parameters={"request_ref": request},
                    )
                )
                with patch.object(h.connectors, "execute", capture):
                    read = h.runtime.run(task.id, h.executive.targets)
                self.assertEqual("partially_verified", read.state)
                research = responses[0].payload["structuredContent"]
                self.assertEqual(accounts[0].id, research["account_id"])
                content = research["answer"]
                writer = mount.capability("mcp.write_file", account_id=accounts[1].id)
                request = h.connectors.stage(
                    {
                        "path": {"name": "write_file"},
                        "body": {"path": "notes.txt", "content": content},
                    }
                )
                worker = h.executive.worker(
                    "Scoped research save",
                    [(mount.node_id, writer.id), (h.node_id, "files.write")],
                    (*grants, "files:write"),
                    owner_authorized=True,
                )
                proposal = h.executive.propose(
                    worker,
                    "Save research to the reviewed workspace",
                    [
                        {
                            "id": "save",
                            "intent": asdict(
                                Intent(
                                    "Save researched notes",
                                    "capability",
                                    capability_kind=writer.id,
                                    parameters={"request_ref": request},
                                    criterion={
                                        "kind": "file_exact",
                                        "path": "notes.txt",
                                        "content": content,
                                    },
                                )
                            ),
                            "depends_on": [],
                            "node_id": mount.node_id,
                            "capability_id": writer.id,
                        },
                        {
                            "id": "archive",
                            "intent": asdict(
                                Intent(
                                    "Archive the verified notes",
                                    "file_write",
                                    "archive.txt",
                                    content,
                                )
                            ),
                            "depends_on": ["save"],
                            "node_id": h.node_id,
                            "capability_id": "files.write",
                        },
                    ],
                )
                h.executive.accept(proposal["id"], proposal["review_digest"], owner_authorized=True)
                with patch.object(h.connectors, "execute", capture):
                    self.assertEqual(0, h.executive.tick())
                    pending = next(t for t in h.store.all("task") if t["id"] != task.id)
                    self.assertEqual("planned", pending["state"])
                    self.assertEqual(1, len(responses))  # No write RPC before Ask approval.
                    self.assertIn(request, h.connectors.requests)
                    self.assertFalse((h.files.root / "notes.txt").exists())
                    review = h.executive.review_task(pending["id"])
                    with self.assertRaises(StateConflict):
                        h.executive.confirm_task(pending["id"], "changed", owner_authorized=True)
                    h.executive.confirm_task(pending["id"], review["digest"], owner_authorized=True)
                    self.assertEqual(2, h.executive.tick())
                self.assertEqual("verified", h.store.task(pending["id"]).state)
                self.assertEqual(2, len(responses))
                self.assertEqual(
                    accounts[1].id, responses[1].payload["structuredContent"]["account_id"]
                )
                self.assertEqual(content, (h.files.root / "notes.txt").read_text())
                for task_id, account in ((task.id, accounts[0]), (pending["id"], accounts[1])):
                    event = next(
                        row for row in h.store.ledger(task_id) if row["event"] == "connector_result"
                    )
                    self.assertEqual(account.id, event["account_id"])
                    self.assertEqual(account.generation, event["account_generation"])
                self.assertNotIn(request, h.connectors.requests)
                # The same reviewed goal continues through the existing native file executor.
                archive = next(
                    row
                    for row in h.store.all("executive_task")
                    if row["goal_id"] == proposal["id"] and row["step_id"] == "archive"
                )
                self.assertEqual("verified", h.store.task(archive["task_id"]).state)
                self.assertEqual(
                    "completed", h.store.get("executive_goal", proposal["id"])["state"]
                )
                self.assertEqual("VERIFIED", h.store.all("artifact")[0]["status"])
                self.assertEqual(content, (h.files.root / "archive.txt").read_text())
                h.plugins.disconnect("writer")
                self.assertFalse(any(c.id == writer.id for c in mount.refresh()))
                self.assertEqual([], h.grid.search(writer.id))
                h.plugins.connect("writer")
                self.assertEqual(writer.id, mount.capability(writer.id).id)
                mount.close()
                with self.assertRaises(PermissionError):
                    h.mount_connectors(
                        "plugins", (*grants, "connectors:destructive"), owner_authorized=True
                    )


if __name__ == "__main__":
    unittest.main()
