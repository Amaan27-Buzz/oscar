"""Real laptop-local Core composition; the enrolled phone is a logical reference fixture."""

import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep

from oscar.commissioning import CommissioningPlan
from oscar.contracts import new_id
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.jev import Intent
from oscar.mobile import Mobile
from oscar.perception import PerceptionSource
from oscar.policy import PersonalPolicy
from oscar.world_model import ObservationKind


class Group03RuntimeTests(unittest.TestCase):
    def test_normal_core_setup_world_presence_executive_surface_and_restart(self):
        with TemporaryDirectory(prefix="oscar-group03-integration-") as folder:
            root = Path(folder)
            state, files = root / "core.sqlite", root / "files"
            manifest = Path("config/development-models.json")
            with Harness(state, files, manifest) as h:
                setup, executive = h.runtime.setup, h.runtime.executive
                identity = setup.commissioning.initialize(owner_authorized=True)
                setup.configure("persona", {"warmth": 80}, owner_authorized=True)
                setup.configure(
                    "preferences",
                    {"reduced_motion": True, "show_presence": True},
                    owner_authorized=True,
                )
                setup.configure("voice", {"local_only": True}, owner_authorized=True)
                scopes = (
                    "heartbeat",
                    "mobile:connect",
                    "mobile:inspect",
                    "presence:read",
                    "executive:read",
                    "world:read",
                    "control:inspect:" + h.node_id,
                )
                h.grid.register(Node("reference-phone", NodeRole.MOBILE, scopes))
                review = setup.commissioning.begin(
                    CommissioningPlan("reference-phone", scopes, simulated=True),
                    owner_authorized=True,
                )
                session = setup.commissioning.pair(
                    review["id"], review["review_digest"], owner_authorized=True
                )
                h.grid.heartbeat(session)
                h.world.configure_source(
                    PerceptionSource(
                        "native-grid",
                        ("core",),
                        ("grid.state",),
                        (ObservationKind.DEVICE,),
                        simulated=False,
                        perceive=True,
                        retain=True,
                    ),
                    "grid",
                    "core",
                    owner_authorized=True,
                )
                h.world.tick()
                h.world.configure_source(
                    PerceptionSource(
                        "native-tasks",
                        ("core",),
                        ("tasks.state",),
                        (ObservationKind.TASK,),
                        simulated=False,
                        perceive=True,
                    ),
                    "tasks",
                    "core",
                    owner_authorized=True,
                )
                worker = executive.worker(
                    "Verified local work",
                    [(h.node_id, "math.add"), (h.node_id, "files.write")],
                    ("math", "files:write"),
                    owner_authorized=True,
                )
                proposal = executive.propose(
                    worker,
                    "Create and verify a local artifact",
                    [
                        {
                            "id": "artifact",
                            "intent": asdict(
                                Intent(
                                    "Create proof",
                                    "file_write",
                                    "proof.txt",
                                    "Core-owned exact bytes",
                                )
                            ),
                            "depends_on": [],
                            "node_id": h.node_id,
                            "capability_id": "files.write",
                        },
                        {
                            "id": "sum",
                            "intent": asdict(Intent("2 + 2")),
                            "depends_on": ["artifact"],
                            "node_id": h.node_id,
                            "capability_id": "math.add",
                        },
                    ],
                )
                executive.accept(proposal["id"], proposal["review_digest"], owner_authorized=True)
                deadline = monotonic() + 5
                while (
                    h.store.get("executive_goal", proposal["id"])["state"] != "completed"
                    and monotonic() < deadline
                ):
                    executive.tick()
                    sleep(0.01)
                self.assertEqual(
                    "completed", h.store.get("executive_goal", proposal["id"])["state"]
                )
                self.assertEqual(b"Core-owned exact bytes", h.files.read("proof.txt"))
                h.world.tick()
                self.assertEqual("current", h.world.world.resolve("core", "tasks.state").state)
                surface = Mobile(
                    h.runtime, PersonalPolicy(h.store), {h.node_id: (h.dispatcher, h.session)}
                )

                def request(operation, payload=None):
                    return surface.request(
                        session,
                        {
                            "version": 1,
                            "request_id": new_id(),
                            "operation": operation,
                            "payload": payload or {},
                        },
                    )

                snapshot = request("snapshot")
                self.assertEqual(2, len(snapshot["tasks"]))
                self.assertEqual("idle", snapshot["presence"]["expression"]["operation"])
                self.assertTrue(snapshot["setup"]["pairing"]["connected"])
                self.assertFalse(snapshot["setup"]["voice"]["operational"])
                self.assertEqual(1, snapshot["executive"]["goals"][0]["verified_runs"])
                task_id = snapshot["tasks"][0]["task_id"]
                adaptive = request(
                    "adaptive", {"task_id": task_id, "supported": ["result_evidence"]}
                )
                self.assertEqual("result_evidence", adaptive["components"][0]["type"])
                self.assertTrue(adaptive["components"][0]["source_ids"])
                self.assertEqual("verified", request("inspect", {"task_id": task_id})["state"])
                current = request("world", {"entity_id": "core", "key": "grid.state"})
                self.assertEqual("world", current["controller_route"])
                self.assertEqual("current", current["current"]["state"])
                self.assertIs(h.archive, h.runtime.memory.archive)
                setup.commissioning.revoke(review["id"], owner_authorized=True)
                with self.assertRaises(PermissionError):
                    request("snapshot")
                h.grid.authenticate(h.session, "execute")
            with Harness(state, files, manifest) as restarted:
                self.assertEqual(
                    identity,
                    restarted.runtime.setup.commissioning.initialize(owner_authorized=True),
                )
                self.assertEqual(80, restarted.runtime.setup.profile("persona")["warmth"])
                self.assertEqual(
                    "completed", restarted.store.get("executive_goal", proposal["id"])["state"]
                )
                self.assertEqual(2, len(restarted.store.all("task")))
                self.assertEqual(b"Core-owned exact bytes", restarted.files.read("proof.txt"))
