# Multi-architecture index verified against Docker Hub on 2026-10-18.
FROM python:3.12.15-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN groupadd --gid 10001 oscar && useradd --uid 10001 --gid 10001 --no-create-home oscar \
    && install -d -o oscar -g oscar -m 0700 /var/lib/oscar
# Remote device proof of possession reuses the existing pinned RSA verifier extra.
COPY --chown=root:root pyproject.toml /app/pyproject.toml
COPY --chown=root:root deploy/cloud/constraints.txt /app/cloud-constraints.txt
COPY --chown=root:root oscar /app/oscar
COPY --chown=root:root config /app/config
RUN python -m pip install --no-cache-dir --only-binary cryptography,cffi,pycparser \
    --constraint /app/cloud-constraints.txt '.[mobile]'
USER 10001:10001
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/readyz', timeout=3).read()"]
CMD ["python", "-m", "oscar.cloud", "--config", "/etc/oscar/cloud.json"]

FROM runtime AS acceptance
COPY --chown=root:root tests /app/tests
COPY --chown=root:root scripts /app/scripts
CMD ["python", "-m", "unittest", "tests.test_cloud", "tests.test_cloud_acceptance", "tests.test_cloud_state", "tests.test_cloud_platform", "tests.test_cloud_recovery", "tests.test_cloud_enrollment", "tests.test_cloud_admission", "tests.test_cloud_diagnostics", "tests.test_remote_enrollment", "tests.test_remote_grid", "tests.test_remote_worker", "tests.test_connected_acceptance", "-v"]

FROM caddy:2.11.7-alpine@sha256:d8542f48d34a9cf4e4c11a478865229840e87e4c96ea3f439101f31a5d35f75f AS ingress
# The stock binary's bind-service file capability prevents exec with cap_drop: ALL.
RUN setcap -r /usr/bin/caddy
USER 10001:10001
