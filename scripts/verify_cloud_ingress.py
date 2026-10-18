"""Exercise actual Core + Caddy TLS on a private Docker network using synthetic data."""

import argparse
import http.client
import json
import re
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from uuid import uuid4

DOMAIN = "ingress-acceptance.invalid"
CORE_ID = "ingress-acceptance-core"


def docker(
    *arguments: str,
    check: bool = True,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["docker", *arguments], input=stdin, capture_output=True, text=True, timeout=60, check=False
    )
    if check and result.returncode:
        # Commands/output may contain fixture credentials; report only safe categories.
        lines = re.findall(r'File "/fixtures/verify.py", line ([0-9]+)', result.stderr)
        rejected = re.findall(r"Grid request rejected \(([0-9]{3})\)", result.stderr)
        detail = f"fixture line {lines[-1]}" if lines else "operation failed"
        if rejected:
            detail += f", Grid HTTP {rejected[-1]}"
        raise RuntimeError(f"Docker {arguments[0]} failed with exit {result.returncode}: {detail}")
    return result


def client() -> None:
    from oscar.remote_client import GridClient

    fixtures = Path("/fixtures")
    credentials = json.load(sys.stdin)
    credential = credentials["diagnostic"]
    identifier = (fixtures / "request-id").read_text()
    context = ssl.create_default_context(cafile=str(fixtures / "ca.crt"))

    redirect = http.client.HTTPConnection(DOMAIN, 8080, timeout=10)
    try:
        redirect.request("GET", "/v1/status", headers={"Host": "untrusted.invalid"})
        response = redirect.getresponse()
        assert response.status == 308
        assert response.getheader("Location") == f"https://{DOMAIN}/v1/status"
        response.read()
    finally:
        redirect.close()

    def request(
        path: str,
        *,
        authenticated: bool = False,
        payload: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        extra = dict(headers or {})
        if authenticated:
            extra.update(
                {
                    "Authorization": "Bearer " + credential["token"],
                    "X-Oscar-Node": credential["node_id"],
                    "X-Oscar-Session": credential["session_id"],
                    "X-Oscar-Nonce": uuid4().hex,
                    "X-Oscar-Time": f"{time.time():.6f}",
                }
            )
        body = json.dumps(payload).encode() if payload is not None else None
        if body is not None:
            extra["Content-Type"] = "application/json"
        message = urllib.request.Request(f"https://{DOMAIN}:8443{path}", body, extra)
        try:
            with urllib.request.urlopen(message, context=context, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as failure:
            data = failure.read()
            return failure.code, json.loads(data) if data else {}

    assert request("/v1/status")[0] == 401, "unauthenticated API was accepted"
    for path in ("/healthz", "/readyz", "/execute", "/sessions", "/debug"):
        assert request(path)[0] == 404, "private/reference endpoint reached ingress"
    code, status = request("/v1/status", authenticated=True)
    assert code == 200 and status["core_id"] == CORE_ID and status["ready"]
    assert status["memory"]["semantic"] == "unavailable"
    assert status["capabilities"]["windows_uia"] == "unavailable"
    code, created = request(
        "/v1/probes",
        authenticated=True,
        payload={"request_id": identifier, "expression": "19 + 23"},
    )
    assert code == 200 and created["value"] == 42, "real Core probe failed"
    code, readback = request("/v1/probes/" + identifier, authenticated=True)
    assert code == 200 and readback == created, "independent TLS readback disagreed"
    grid = GridClient(
        f"https://{DOMAIN}:8443",
        credentials["remote"],
        fixture_signer(fixtures),
        ssl_context=context,
    )
    snapshot = grid.request("snapshot", {"cursor": 0})
    assert snapshot["core_id"] == CORE_ID
    remote = grid.request(
        "submit",
        {
            "text": "synthetic TLS arithmetic acceptance",
            "kind": "addition",
            "target": CORE_ID,
            "parameters": {"expression": "19 + 23"},
            "retain": True,
        },
        request_id=identifier,
    )
    deadline = time.monotonic() + 20
    while True:
        inspected = grid.request("inspect", {"task_id": remote["task_id"]})
        if inspected["state"] in {"verified", "blocked", "failed", "unknown"}:
            break
        assert time.monotonic() < deadline, "bounded Grid task did not finish"
        time.sleep(1)
    assert inspected["state"] == "verified" and inspected["evidence"]
    assert inspected["result"]["value"] == "42", "Grid result did not match real arithmetic"
    print(
        json.dumps(
            {
                "tls_verified": True,
                "task_id": created["task_id"],
                "remote_task_id": remote["task_id"],
            }
        )
    )


def remote_enroll() -> None:
    """Private pipe IPC for generated test credentials; never production diagnostics."""
    from oscar.remote_client import GridClient

    fixtures = Path("/fixtures")
    client = GridClient(
        f"https://{DOMAIN}:8443",
        {},
        fixture_signer(fixtures),
        ssl_context=ssl.create_default_context(cafile=str(fixtures / "ca.crt")),
    )
    print(json.dumps(client.enroll(json.load(sys.stdin))))


def fixture_signer(fixtures: Path) -> Callable[[bytes], bytes]:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    key = serialization.load_pem_private_key((fixtures / "grid-key.pem").read_bytes(), None)
    assert isinstance(key, rsa.RSAPrivateKey)
    return lambda payload: key.sign(
        payload,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
        hashes.SHA256(),
    )


def wait_for_core(name: str) -> None:
    deadline = time.monotonic() + 30
    health = (
        "import urllib.request; "
        "urllib.request.urlopen('http://127.0.0.1:8080/readyz', timeout=2).read()"
    )
    while time.monotonic() < deadline:
        state = json.loads(docker("inspect", name).stdout)[0]["State"]
        if not state["Running"]:
            raise RuntimeError("Core failed production configuration or lifecycle startup")
        if docker("exec", name, "python", "-c", health, check=False).returncode == 0:
            return
        time.sleep(0.2)
    raise RuntimeError("Core did not become ready within the startup bound")


def verify(core_image: str, ingress_image: str) -> None:
    import base64

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    if not shutil.which("docker"):
        raise RuntimeError("Docker CLI and a running Linux daemon are required")
    repository = Path(__file__).resolve().parents[1]
    prefix = "oscar-d1-tls-" + uuid4().hex[:12]
    network, volume = prefix + "-network", prefix + "-data"
    core_name, proxy_name = prefix + "-core", prefix + "-proxy"
    common = [
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--pids-limit",
        "128",
        "--tmpfs",
        "/tmp:rw,size=64m,mode=1777",
    ]
    core_options = [*common, "--memory", "1g", "--cpus", "1"]
    ingress_options = [*common, "--memory", "256m", "--cpus", "0.5"]
    try:
        with TemporaryDirectory(prefix=prefix) as temporary:
            fixtures = Path(temporary)
            # Only generated fixtures: the container UID must traverse this mount.
            fixtures.chmod(0o755)
            config = {
                "version": 1,
                "environment": "production",
                "core_id": CORE_ID,
                "data_dir": "/var/lib/oscar",
                "manifest": "/app/config/development-models.json",
                "secret_dir": "/run/secrets/oscar",
                "listen_host": "0.0.0.0",
                "listen_port": 8080,
                "ingress": "tls-proxy",
                "allowed_hosts": [DOMAIN, "core", "127.0.0.1"],
                "provider_secrets": {},
            }
            (fixtures / "cloud.json").write_text(json.dumps(config), encoding="utf-8")
            production = (repository / "deploy/cloud/Caddyfile").read_text(encoding="utf-8")
            assert production.count("{$OSCAR_DOMAIN} {") == 1
            (fixtures / "Caddyfile").write_text(
                production.replace("{$OSCAR_DOMAIN} {", "{$OSCAR_DOMAIN} {\n\ttls internal"),
                encoding="utf-8",
            )
            (fixtures / "request-id").write_text(uuid4().hex)
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            (fixtures / "grid-key.pem").write_bytes(
                key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
            (fixtures / "grid-public.txt").write_text(
                base64.b64encode(
                    key.public_key().public_bytes(
                        serialization.Encoding.DER,
                        serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                ).decode(),
                encoding="ascii",
            )
            shutil.copyfile(__file__, fixtures / "verify.py")
            for path in fixtures.iterdir():
                path.chmod(0o644)
            mount = ["--volume", f"{fixtures}:/fixtures:ro"]
            docker("network", "create", "--internal", network)
            docker("volume", "create", volume)
            storage = [
                "--mount",
                f"type=volume,source={volume},target=/var/lib/oscar",
                "--tmpfs",
                "/run/secrets/oscar:rw,size=1m,mode=0700,uid=10001,gid=10001",
            ]
            command = ["python", "-m", "oscar.cloud", "--config", "/fixtures/cloud.json"]
            docker(
                "run",
                "--rm",
                "--network",
                "none",
                *core_options,
                *mount,
                *storage,
                core_image,
                *command,
                "--initialize",
            )
            docker(
                "run",
                "--rm",
                "--network",
                "none",
                *core_options,
                *mount,
                *storage,
                core_image,
                *command,
                "--enroll-client",
                "--node-id",
                "ingress-acceptance-client",
                "--credential-output",
                "/var/lib/oscar/fixture-client.json",
                "--ttl",
                "3600",
            )
            docker(
                "run",
                "--rm",
                "--network",
                "none",
                *core_options,
                *mount,
                *storage,
                core_image,
                "python",
                "-c",
                "import json; from pathlib import Path; "
                "from oscar.cloud import CloudConfig,CloudCore; "
                "from oscar.remote_grid import create_invitation; "
                "config=CloudConfig.load(Path('/fixtures/cloud.json')); "
                "core=CloudCore(config,start_services=False); "
                "invite=create_invitation(core,'ingress-grid-mobile','mobile','ingress-install',"
                "Path('/fixtures/grid-public.txt').read_text(),retain=True); "
                "Path('/var/lib/oscar/fixture-invitation.json').write_text(json.dumps(invite)); "
                "core.close()",
            )
            docker(
                "run",
                "--detach",
                "--name",
                core_name,
                "--network",
                network,
                "--network-alias",
                "core",
                *core_options,
                *mount,
                *storage,
                core_image,
                *command,
            )
            wait_for_core(core_name)
            credential = docker(
                "exec",
                core_name,
                "python",
                "-c",
                "from pathlib import Path; "
                "print(Path('/var/lib/oscar/fixture-client.json').read_text())",
            ).stdout
            docker(
                "run",
                "--detach",
                "--name",
                proxy_name,
                "--network",
                network,
                "--network-alias",
                DOMAIN,
                *ingress_options,
                *mount,
                "--env",
                "OSCAR_DOMAIN=" + DOMAIN,
                "--tmpfs",
                "/data:rw,size=32m,mode=0700,uid=10001,gid=10001",
                "--tmpfs",
                "/config:rw,size=16m,mode=0700,uid=10001,gid=10001",
                ingress_image,
                "caddy",
                "run",
                "--config",
                "/fixtures/Caddyfile",
                "--adapter",
                "caddyfile",
            )
            deadline = time.monotonic() + 20
            while True:
                copied = docker(
                    "exec",
                    proxy_name,
                    "cat",
                    "/data/caddy/pki/authorities/local/root.crt",
                    check=False,
                )
                if copied.returncode == 0:
                    (fixtures / "ca.crt").write_text(copied.stdout, encoding="ascii")
                    (fixtures / "ca.crt").chmod(0o644)
                    break
                if time.monotonic() >= deadline:
                    # No client request has occurred; only synthetic TLS startup logs exist.
                    logs = docker("logs", "--tail", "8", proxy_name, check=False)
                    raise RuntimeError("TLS ingress failed local CA initialization: " + logs.stderr)
                time.sleep(0.2)
            for name in (core_name, proxy_name):
                info = json.loads(docker("inspect", name).stdout)[0]
                assert not info["HostConfig"]["PortBindings"], "unexpected published port"
                assert info["Config"]["User"] == "10001:10001", "unexpected service identity"
                assert info["HostConfig"]["ReadonlyRootfs"], "writable container image"
                assert "ALL" in info["HostConfig"]["CapDrop"], "unexpected process capabilities"
            check = [
                "run",
                "--rm",
                "--interactive",
                "--network",
                network,
                *core_options,
                *mount,
                core_image,
                "python",
                "/fixtures/verify.py",
                "--client",
            ]
            invitation = docker(
                "exec",
                core_name,
                "python",
                "-c",
                "from pathlib import Path; "
                "print(Path('/var/lib/oscar/fixture-invitation.json').read_text())",
            ).stdout
            remote_session = docker(*[*check[:-1], "--remote-enroll"], stdin=invitation).stdout
            credentials = json.dumps(
                {
                    "diagnostic": json.loads(credential),
                    "remote": json.loads(remote_session),
                }
            )
            first = json.loads(docker(*check, stdin=credentials).stdout)
            docker("restart", "--time", "10", core_name)
            wait_for_core(core_name)
            second = json.loads(docker(*check, stdin=credentials).stdout)
            assert first == second, "restart duplicated the same request's Core task"
            snapshots = docker(
                "stats",
                "--no-stream",
                "--format",
                "{{json .}}",
                core_name,
                proxy_name,
            ).stdout.splitlines()
            memory = {}
            for line in snapshots:
                item = json.loads(line)
                role = "core" if item["Name"] == core_name else "ingress"
                memory[role] = item["MemUsage"]
    finally:
        docker("rm", "--force", core_name, proxy_name, check=False)
        docker("volume", "rm", volume, check=False)
        docker("network", "rm", network, check=False)
    print(
        json.dumps(
            {
                "status": "verified",
                "tls": "trusted-local-ca",
                "network": "private-no-published-ports",
                "restart_readback": True,
                "grid_protocol": 2,
                "container_memory_snapshot": memory,
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-image", default="oscar-cloud:local")
    parser.add_argument("--ingress-image", default="oscar-cloud-ingress:local")
    parser.add_argument("--client", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--remote-enroll", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.remote_enroll:
        remote_enroll()
    elif args.client:
        client()
    else:
        verify(args.core_image, args.ingress_image)


if __name__ == "__main__":
    main()
