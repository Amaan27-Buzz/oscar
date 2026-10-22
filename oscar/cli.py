"""Explicit developer commands; live calls are opt-in and never load/write a .env file."""

import argparse
import json
from dataclasses import asdict, replace
from pathlib import Path
from time import sleep
from urllib.parse import urlparse

from .capabilities import Cancellation
from .contracts import Action, Result, TaskState, new_id, record
from .harness import Harness
from .jev import Intent
from .models import Mode, ModelRequest, ProviderError, RoutingPolicy
from .perception import PerceptionSource
from .router import RouteUnavailable
from .storage import StateConflict
from .transport import HTTPTransport, ReferenceServer
from .world_model import ObservationKind


def print_json(value: object) -> None:
    print(json.dumps(value, indent=2, allow_nan=False))


def report_task(harness: Harness, task_id: str) -> dict[str, object]:
    task = harness.store.task(task_id)
    return {
        "task": record(task),
        "ledger": harness.store.ledger(task.id),
        "evidence": [e for e in harness.store.all("evidence") if e["task_id"] == task.id],
        "artifacts": [a for a in harness.store.all("artifact") if a["task_id"] == task.id],
    }


def fake_executor(action: Action, cancellation: Cancellation) -> Result:
    cancellation.check()
    return Result(
        new_id(),
        action.id,
        action.task_id,
        action.correlation_id,
        "deliberately-fake-reference-executor",
        True,
    )


def proof(harness: Harness) -> dict[str, object]:
    with ReferenceServer(harness.dispatcher) as server:
        transports = {harness.node_id: (HTTPTransport(server.url), harness.session)}
        task = harness.runtime.create(
            Intent(
                "Gate A exact file",
                "file_write",
                "proof/" + new_id() + ".txt",
                "OSCAR verified bytes\n",
            )
        )
        actual = harness.runtime.run(task.id, transports)
        arithmetic = harness.runtime.create(Intent("what is 2 + 2?"))
        arithmetic = harness.runtime.run(arithmetic.id, transports)
        original = harness.dispatcher.executors["files.write"]
        harness.dispatcher.executors["files.write"] = fake_executor
        try:
            fake = harness.runtime.create(
                Intent(
                    "Deliberate fake-success test",
                    "file_write",
                    "proof/absent-" + new_id() + ".txt",
                    "never written",
                )
            )
            fake = harness.runtime.run(fake.id, transports)
        finally:
            harness.dispatcher.executors["files.write"] = original
    passed = (
        actual.state == TaskState.VERIFIED
        and arithmetic.state == TaskState.VERIFIED
        and fake.state == TaskState.FAILED
    )
    return {
        "status": "VERIFIED" if passed else "FAILED",
        "scope": "loopback HTTP, exact file verification, fake rejection and arithmetic",
        "real_file": report_task(harness, actual.id),
        "fake_executor": report_task(harness, fake.id),
        "deterministic": report_task(harness, arithmetic.id),
    }


def grid_proof(harness: Harness) -> dict[str, object]:
    task = harness.runtime.create(Intent("Lease loss proof", "file_write", "lease.txt", "test"))
    harness.store.transition(task.id, TaskState.EXECUTING)
    lease = harness.grid.lease(task.id, harness.node_id, ttl=0.05)
    harness.grid.disconnect(harness.node_id)
    before = harness.store.task(task.id).state
    sleep(0.06)
    expired = harness.grid.reap()
    return {
        "scope": "reference node; no physical device",
        "task_id": task.id,
        "state_after_disconnect": before,
        "state_after_expiry": harness.store.task(task.id).state,
        "lease_active": harness.store.get("lease", lease)["active"],
        "expired_tasks": expired,
        "objective_preserved": bool(harness.store.get("objective", task.objective_id)),
        "availability": harness.grid.availability(),
        "nodes": harness.grid.nodes(),
    }


def live_providers(harness: Harness, report_path: Path) -> list[dict[str, object]]:
    for line in harness.pool.safe_presence_lines():
        print(line)
    results: list[dict[str, object]] = []
    for provider in harness.registry.providers.values():
        slots = [s for s in harness.pool.slots.values() if s.provider == provider.id and s.present]
        hostname = urlparse(provider.base_url).hostname
        result: dict[str, object] = {
            "provider": provider.id,
            "hostname": hostname,
            "status": "UNAVAILABLE",
            "slots_exercised": [],
            "model": None,
        }
        if not slots:
            result["reason"] = "no runtime credential slot present"
            results.append(result)
            continue
        models = sorted(
            (m for m in harness.registry.models.values() if m.provider_id == provider.id),
            key=lambda m: (m.quality or 99, m.id),
        )
        if not models:
            result["reason"] = "no configured model metadata"
            results.append(result)
            continue
        request = ModelRequest(
            new_id(),
            new_id(),
            "Reply exactly OSCAR_PROVIDER_OK",
            mode=Mode.MANUAL,
            pinned_provider=provider.id,
            pinned_model=models[0].id,
            max_output_tokens=32,
        )
        if not harness.router.rank(request):
            # Read-only discovery can diagnose access without assuming unknown price is free.
            result.update(operation="model inventory GET", slots_exercised=[slots[0].id])
            try:
                discovered = harness.adapters[provider.adapter].discover(
                    provider, harness.pool.secret_for_adapter(slots[0].id)
                )
                result.update(
                    status="PARTIALLY_VERIFIED",
                    reason="inventory reachable; generation cost policy unresolved",
                    discovered_model_count=len(discovered),
                )
            except ProviderError as error:
                result.update(status="BLOCKED", reason=error.category.value)
        else:
            result.update(operation="generation POST", model=models[0].id)
            try:
                routed = harness.router.execute(
                    request, RoutingPolicy(max_attempts=2, timeout_seconds=10)
                )
                matches = routed.response.text.strip() == "OSCAR_PROVIDER_OK"
                result.update(
                    status="VERIFIED" if matches else "PARTIALLY_VERIFIED",
                    reason="independent sentinel comparison: "
                    + ("matched" if matches else "did not match"),
                    scope="provider generation contract only; general objective quality unverified",
                )
            except ProviderError as error:
                result.update(
                    status="BLOCKED"
                    if error.category.value.startswith("network")
                    else "UNAVAILABLE",
                    reason=error.category.value,
                )
            except RouteUnavailable:
                result.update(status="UNAVAILABLE", reason="no current route permitted")
            result["slots_exercised"] = [
                event["slot"]
                for event in harness.store.all("route_history")
                if event["task_id"] == request.task_id
            ]
        if result.get("reason") == "network_policy_blocked":
            result["required_configuration"] = (
                f"Allow HTTPS egress to {hostname} in the environment policy; preserve proxy/TLS."
            )
        results.append(result)
    report_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    report_path.write_text(json.dumps(results, indent=2) + "\n")
    report_path.chmod(0o600)
    return results


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--state", type=Path, default=Path(".oscar/state.sqlite"))
    result.add_argument("--workspace", type=Path, default=Path(".oscar/workspace"))
    result.add_argument("--manifest", type=Path, default=Path("config/development-models.json"))
    result.add_argument("--auth-config", type=Path)
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("credentials")
    commands.add_parser("proof")
    commands.add_parser("grid-proof")
    commands.add_parser("history")
    commands.add_parser("sources")
    executive = commands.add_parser("executive")
    executive.add_argument("--config", type=Path)
    setup = commands.add_parser("setup")
    setup.add_argument(
        "--section",
        choices=(
            "identity",
            "persona",
            "preferences",
            "voice",
            "policy",
            "sentry",
            "source",
            "recover",
        ),
    )
    setup.add_argument("--config", type=Path)
    provider = commands.add_parser("setup-provider")
    provider.add_argument("slot")
    provider.add_argument("--revoke", action="store_true")
    world = commands.add_parser("world")
    world.add_argument("--entity", required=True)
    world.add_argument("--key", required=True)
    watch = commands.add_parser("watch-core")
    watch.add_argument("source", choices=("grid", "tasks"))
    watch.add_argument("--retain", action="store_true")
    serve = commands.add_parser("serve")
    serve.add_argument("--seconds", type=int, default=3600)
    serve.add_argument("--voice-config", type=Path)
    serve.add_argument(
        "--continuous-voice",
        metavar="SESSION_ID",
        help=(
            "Grant continuous microphone perception to one existing Desktop session; "
            "never starts capture"
        ),
    )
    serve.add_argument(
        "--reenroll-execution",
        action="store_true",
        help="Explicit trusted-local execution enrollment after credential expiry/revocation",
    )
    write = commands.add_parser("write")
    write.add_argument("--path", required=True)
    write.add_argument("--content", required=True)
    write.add_argument("--http-reference", action="store_true")
    ask = commands.add_parser("ask")
    ask.add_argument("text")
    for command in ("reason", "routes"):
        route = commands.add_parser(command)
        if command == "reason":
            route.add_argument("text")
        route.add_argument("--mode", choices=list(Mode), default=Mode.AUTO)
        route.add_argument("--provider")
        route.add_argument("--model")
        route.add_argument("--slot")
        route.add_argument("--quality", type=int, default=1)
        route.add_argument("--task-class", default="reasoning")
    for command in ("inspect", "cancel", "resume"):
        task = commands.add_parser(command)
        task.add_argument("task_id")
    live = commands.add_parser("live-providers")
    live.add_argument("--report", type=Path, default=Path(".oscar/live-providers.json"))
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        template = None
        if args.command in {"reason", "routes"}:
            template = ModelRequest(
                new_id(),
                new_id(),
                getattr(args, "text", ""),
                task_class=args.task_class,
                min_quality=args.quality,
                mode=Mode(args.mode),
                pinned_provider=args.provider,
                pinned_model=args.model,
                pinned_slot=args.slot,
            )
        with Harness(
            args.state,
            args.workspace,
            args.manifest,
            template,
            execution_enrollment_authorized=getattr(args, "reenroll_execution", False),
            auth_config=args.auth_config,
        ) as harness:
            transports = {harness.node_id: (harness.dispatcher, harness.session)}
            if args.command == "executive":
                executive = harness.runtime.executive
                assert executive is not None
                result: object = None
                if args.config is not None:
                    if args.config.stat().st_size > 32768:
                        raise ValueError("bounded selected Executive command required")
                    config = json.loads(args.config.read_text(encoding="utf-8"))
                    operation = config.pop("operation")
                    if operation == "worker":
                        config["capabilities"] = [tuple(c) for c in config["capabilities"]]
                        config["grants"] = tuple(config["grants"])
                        result = executive.worker(**config, owner_authorized=True)
                    elif operation == "propose":
                        result = executive.propose(**config)
                    elif operation == "decompose":
                        result = executive.decompose(**config)
                    elif operation == "draft_plan":
                        result = executive.draft_plan(**config)
                    elif operation == "propose_from_result":
                        result = executive.propose_from_result(**config)
                    elif operation == "accept":
                        executive.accept(**config, owner_authorized=True)
                    elif operation in {"pause", "resume", "cancel"}:
                        executive.control(**config, operation=operation, owner_authorized=True)
                    elif operation == "retry":
                        executive.retry(**config, owner_authorized=True)
                    elif operation == "review_task":
                        result = executive.review_task(**config)
                    elif operation == "confirm_task":
                        executive.confirm_task(**config, owner_authorized=True)
                    elif operation == "revoke_worker":
                        executive.revoke_worker(**config, owner_authorized=True)
                    elif operation == "replan":
                        result = executive.replan(**config, owner_authorized=True)
                    elif operation == "learn":
                        result = executive.learn(**config, owner_authorized=True)
                    elif operation == "reuse":
                        result = executive.reuse(**config, owner_authorized=True)
                    elif operation == "evaluate_workflow":
                        result = executive.evaluate_workflow(**config, owner_authorized=True)
                    elif operation == "rebuild_workflows":
                        result = executive.rebuild_workflows(owner_authorized=True)
                    else:
                        raise ValueError("unsupported Executive operation")
                executive.tick()
                print_json({"result": result, "executive": executive.snapshot()})
            elif args.command in {"setup", "setup-provider"}:
                setup = harness.runtime.setup
                assert setup is not None
                if args.command == "setup-provider":
                    if args.revoke:
                        setup.revoke_provider(args.slot, owner_authorized=True)
                    else:
                        from getpass import getpass

                        setup.provider(
                            args.slot,
                            getpass("Provider credential (native Vault only): "),
                            owner_authorized=True,
                        )
                elif args.section in {"identity", "recover"}:
                    if args.section == "identity":
                        setup.commissioning.initialize(owner_authorized=True)
                    else:
                        setup.recover()
                elif args.section:
                    if args.config is None or args.config.stat().st_size > 8192:
                        raise ValueError("bounded selected setup configuration required")
                    config = json.loads(args.config.read_text(encoding="utf-8"))
                    if args.section == "policy":
                        from .policy import PolicyEffect, PolicyRule

                        setup.policy(
                            PolicyRule(**{**config, "effect": PolicyEffect(config["effect"])}),
                            owner_authorized=True,
                        )
                    elif args.section == "sentry":
                        from .sentry import AwarenessMode, SentrySettings, SentryState

                        harness.world.sentry.configure(
                            SentrySettings(
                                **{
                                    **config,
                                    "mode": AwarenessMode(config["mode"]),
                                    "state": SentryState(config["state"]),
                                    "source_ids": tuple(config.get("source_ids", ())),
                                    "trigger_keys": tuple(config.get("trigger_keys", ())),
                                }
                            ),
                            owner_authorized=True,
                        )
                    elif args.section == "source":
                        source = config.pop("source")
                        harness.world.configure_source(
                            PerceptionSource(
                                **{
                                    **source,
                                    "entities": tuple(source["entities"]),
                                    "keys": tuple(source["keys"]),
                                    "kinds": tuple(ObservationKind(k) for k in source["kinds"]),
                                }
                            ),
                            **config,
                            owner_authorized=True,
                        )
                    else:
                        setup.configure(args.section, config, owner_authorized=True)
                print_json(setup.snapshot())
            elif args.command == "serve":
                from threading import Event

                from .desktop import Desktop
                from .mobile import Mobile, MobileServer
                from .policy import PersonalPolicy

                if not 1 <= args.seconds <= 86400:
                    raise ValueError("bounded local serving lifetime required")
                desktop_core = Desktop(harness.runtime, PersonalPolicy(harness.store), transports)
                if args.voice_config is not None:
                    from .desktop_voice import configured_voice

                    desktop_core.voice = configured_voice(desktop_core, args.voice_config)
                if args.continuous_voice is not None:
                    if desktop_core.voice is None:
                        raise ValueError("continuous voice grant requires --voice-config")
                    from .desktop_voice import grant_continuous_voice

                    grant_continuous_voice(desktop_core, args.continuous_voice)
                with (
                    MobileServer(
                        Mobile(harness.runtime, PersonalPolicy(harness.store), transports)
                    ) as mobile,
                    MobileServer(desktop_core) as desktop,
                ):
                    print_json(
                        {
                            "mobile_url": mobile.url,
                            "desktop_url": desktop.url,
                            "scope": "authenticated loopback Core; no device enrollment inferred",
                        }
                    )
                    try:
                        Event().wait(args.seconds)
                    except KeyboardInterrupt:
                        pass
                    finally:
                        if desktop_core.voice is not None:
                            desktop_core.voice.close()
            elif args.command in {"sources", "world", "watch-core"}:
                if harness.runtime.world is None:
                    raise StateConflict("current-state runtime unavailable")
                if args.command == "watch-core":
                    grid_source = args.source == "grid"
                    harness.runtime.world.configure_source(
                        PerceptionSource(
                            "core-" + args.source,
                            ("core",),
                            (args.source + ".state",),
                            (ObservationKind.DEVICE if grid_source else ObservationKind.TASK,),
                            simulated=False,
                            perceive=True,
                            retain=args.retain,
                        ),
                        args.source,
                        "core",
                        owner_authorized=True,
                    )
                    harness.runtime.world.tick()
                print_json(
                    harness.runtime.current(args.entity, args.key)
                    if args.command == "world"
                    else harness.runtime.world.snapshot()
                )
            elif args.command == "credentials":
                for line in harness.pool.safe_presence_lines():
                    print(line)
            elif args.command == "proof":
                data = proof(harness)
                print_json(data)
                return 0 if data["status"] == "VERIFIED" else 1
            elif args.command == "grid-proof":
                print_json(grid_proof(harness))
            elif args.command == "live-providers":
                print_json(live_providers(harness, args.report))
            elif args.command == "history":
                print_json(harness.store.all("route_history"))
            elif args.command == "routes" and template:
                print_json([asdict(r) for r in harness.router.rank(template)])
            elif args.command in {"inspect", "cancel", "resume"}:
                if args.command == "cancel":
                    harness.runtime.cancel(args.task_id)
                elif args.command == "resume":
                    harness.grid.reap()
                    harness.runtime.reclaim(args.task_id)
                    harness.runtime.run(args.task_id, transports)
                print_json(report_task(harness, args.task_id))
            else:
                intent = (
                    Intent(args.text)
                    if args.command in {"ask", "reason"}
                    else Intent("Write exact file", "file_write", args.path, args.content)
                )
                if args.command == "reason":
                    intent = replace(intent, kind="reason")
                task = harness.runtime.create(intent, mode=getattr(args, "mode", "auto"))
                if getattr(args, "http_reference", False):
                    with ReferenceServer(harness.dispatcher) as server:
                        task = harness.runtime.run(
                            task.id, {harness.node_id: (HTTPTransport(server.url), harness.session)}
                        )
                else:
                    task = harness.runtime.run(task.id, transports)
                print_json(report_task(harness, task.id))
                return 0 if task.state == TaskState.VERIFIED else 2
    except StateConflict as conflict:
        print_json({"status": "BLOCKED", "reason": str(conflict)})
        return 2
    except (ValueError, TypeError, KeyError, PermissionError, OSError):
        print_json(
            {
                "status": "BLOCKED",
                "reason": "invalid configuration or unavailable state; inspect command inputs",
            }
        )
        return 2
    return 0
