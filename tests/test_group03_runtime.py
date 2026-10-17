"""Real laptop-local Core composition; the enrolled phone is a logical reference fixture."""

import subprocess
import sys
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep, time

from oscar.commissioning import CommissioningPlan
from oscar.contracts import new_id
from oscar.grid import Node, NodeRole
from oscar.harness import Harness
from oscar.jev import Intent
from oscar.mobile import Mobile
from oscar.perception import PerceptionSource
from oscar.policy import PersonalPolicy
from oscar.world_model import ObservationKind
from tests.support import Clock


class Group03RuntimeTests(unittest.TestCase):
    def test_day_of_core_world_presence_and_workers_with_source_loss(self):
        with TemporaryDirectory(prefix="oscar-day-integration-") as folder:
            root = Path(folder)
            clock = Clock()
            with Harness(
                root / "core.sqlite",
                root / "files",
                Path("config/development-models.json"),
                clock=clock,
            ) as h:

                def enroll_source():
                    h.world.configure_source(
                        PerceptionSource(
                            "uptime-tasks",
                            ("core",),
                            ("tasks.state",),
                            (ObservationKind.TASK,),
                            perceive=True,
                            simulated=False,
                        ),
                        "tasks",
                        "core",
                        owner_authorized=True,
                    )

                enroll_source()
                executive = h.executive
                worker = executive.worker(
                    "Hourly local work", [(h.node_id, "math.add")], ("math",), owner_authorized=True
                )
                goal = executive.decompose(worker, "2 + 2", interval_seconds=3600, max_runs=25)
                executive.accept(goal["id"], goal["review_digest"], owner_authorized=True)
                start = clock()
                for minute in range(0, 1441, 5):
                    clock.now = start + minute * 60
                    h.grid.maintain_internal(h.session)
                    if minute == 480:
                        h.world.fabric.revoke("uptime-tasks", owner_authorized=True)
                    if minute == 600:
                        enroll_source()
                    h.world.tick()
                    executive.tick()
                    # Settle every due occurrence before advancing the simulated clock.
                    if minute % 60 == 0:
                        expected = minute // 60 + 1
                        deadline = monotonic() + 5
                        while (
                            h.store.get("executive_goal", goal["id"])["run_index"] < expected
                            and monotonic() < deadline
                        ):
                            executive.tick()
                            sleep(0.002)
                        self.assertEqual(
                            expected, h.store.get("executive_goal", goal["id"])["run_index"]
                        )
                    if minute in {60, 120, 480, 1440}:
                        h.world.tick()
                        current = h.world.world.resolve("core", "tasks.state")
                        self.assertEqual(minute != 480, current.state == "current")
                        self.assertEqual(
                            "idle", h.runtime.presence.snapshot()["expression"]["operation"]
                        )
                self.assertEqual(25, len(h.store.all("action")))
                self.assertTrue(all(t["state"] == "verified" for t in h.store.all("task")))
                self.assertIs(h.archive, h.runtime.memory.archive)

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

    def test_process_crash_after_file_mutation_does_not_replay_on_restart(self):
        script = """
import sys
from dataclasses import asdict
from pathlib import Path
from threading import Event
from oscar.harness import Harness
from oscar.jev import Intent
root = Path(sys.argv[1])
with Harness(root/'core.sqlite', root/'files', Path('config/development-models.json')) as h:
    original = h.dispatcher.executors['files.write']
    def interrupted(action, cancellation):
        original(action, cancellation)
        (root/'ready').write_text('mutation completed', encoding='utf-8')
        Event().wait(30)
        raise OSError('result lost')
    h.dispatcher.executors['files.write'] = interrupted
    e = h.executive
    w = e.worker('Crash proof', [(h.node_id,'files.write')],
                 ('files:write',), owner_authorized=True)
    step = {'id':'proof', 'intent':asdict(Intent('Write','file_write','proof.txt','once')),
            'depends_on':[], 'node_id':h.node_id, 'capability_id':'files.write'}
    g = e.propose(w, 'Exact mutation', [step])
    e.accept(g['id'], g['review_digest'], owner_authorized=True)
    e.tick()
"""
        with TemporaryDirectory(prefix="oscar-active-crash-") as folder:
            root = Path(folder)
            process = subprocess.Popen(
                [sys.executable, "-c", script, str(root)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                deadline = monotonic() + 10
                while (
                    not (root / "ready").exists()
                    and process.poll() is None
                    and monotonic() < deadline
                ):
                    sleep(0.02)
                self.assertTrue((root / "ready").exists(), "Child did not reach the real mutation")
                stamp = (root / "files/proof.txt").stat().st_mtime_ns
            finally:
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=5)
            with Harness(
                root / "core.sqlite",
                root / "files",
                Path("config/development-models.json"),
                clock=lambda: time() + 121,
            ) as h:
                calls = []
                original = h.dispatcher.executors["files.write"]

                def count(action, cancellation):
                    calls.append(action.id)
                    return original(action, cancellation)

                h.dispatcher.executors["files.write"] = count
                h.grid.reap()
                task = h.store.all("task")[0]
                self.assertEqual("blocked", task["state"])
                h.executive.retry(task["id"], owner_authorized=True)
                h.executive.tick()
                self.assertFalse(calls)
                self.assertEqual(stamp, (root / "files/proof.txt").stat().st_mtime_ns)
                self.assertEqual(b"once", h.files.read("proof.txt"))
                self.assertEqual(1, len(h.store.all("action")))
                self.assertNotEqual("verified", h.store.task(task["id"]).state)
