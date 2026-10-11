# Dependency update — 2026-10-11

This update preserves Pulliku's API, account/session model, SQLite schema and media-download settings. All four workflows and the weekly Dependabot schedule remain enabled, as requested after the notification was identified as belonging to other applications.

## Stable release inventory

| Dependency | Previous input | Updated input | Authoritative source |
| --- | --- | --- | --- |
| FastAPI | 0.141.1 | 0.143.0 | [PyPI](https://pypi.org/project/fastapi/0.143.0/) |
| Uvicorn | 0.52.4 | 0.54.0 | [PyPI](https://pypi.org/project/uvicorn/0.54.0/) |
| httpx2 (tests) | 2.12.0 | 2.13.1 | [PyPI](https://pypi.org/project/httpx2/2.13.1/) |
| Alpine (builder/runtime) | 3.23 | 3.24.2 | [Alpine downloads](https://alpinelinux.org/downloads/) |
| Deno | 2.8.3 | 2.9.7 | [Release](https://github.com/denoland/deno/releases/tag/v2.9.7) |
| actions/checkout | v6 | v7.0.1 | [Release](https://github.com/actions/checkout/releases/tag/v7.0.1) |
| actions/setup-node | v6 | v7.1.0 | [Release](https://github.com/actions/setup-node/releases/tag/v7.1.0) |
| actions/upload-artifact (verification / discovery) | v7.0.1 / v4 | v7.0.2 | [Release](https://github.com/actions/upload-artifact/releases/tag/v7.0.2) |
| docker/setup-qemu-action | v4 | v4.4.0 | [Release](https://github.com/docker/setup-qemu-action/releases/tag/v4.4.0) |
| docker/setup-buildx-action | v4.3.0 | v4.4.1 | [Release](https://github.com/docker/setup-buildx-action/releases/tag/v4.4.1) |
| docker/build-push-action | v7.3.0 | v7.4.0 | [Release](https://github.com/docker/build-push-action/releases/tag/v7.4.0) |
| actions/attest-build-provenance | v3 | v4.2.2 | [Release](https://github.com/actions/attest-build-provenance/releases/tag/v4.2.2) |

Already at the latest stable release: python-multipart 0.0.32, argon2-cffi 25.1.0, yt-dlp 2026.8.19, AtomicParsley 20240608.083822.1ed9031, docker/login-action v4.6.0 and aquasecurity/trivy-action v0.36.0. AtomicParsley's existing full commit remains pinned. No nightly or prerelease inputs were selected.

Docker Hub supplied these multi-platform index digests, including amd64 and arm64:

- Alpine: `sha256:fd791d74b68913cbb027c6546007b3f0d3bc45125f797758156952bc2d6daf40` → `sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6`.
- Deno: `sha256:9eb3b9b8bd4f821de57239792f76f6a3bef29a7bfbd486b801cbf34fc2c32797` → `sha256:8ce780168429c4bf5962652e6cbea3fd45254ae902069e90585fb33f74c56968`.

Every action remains pinned to the release's full commit SHA. The app-local kit manifest and lock record the changed workflow checksums and the reason for the local update; verification code and policies are unchanged.

## Compatibility, licenses and security

FastAPI's new opt-in telemetry exporter configuration does not affect this app, which does not configure telemetry. Uvicorn's experimental HTTP/2 features remain disabled. Checkout v7's changes to privileged fork handling do not affect the existing triggers; setup-node's token changes do not affect this app's Node-only verification setup. Hosted Ubuntu runners support the Node 24 action runtime. Provenance v4 retains the existing input interface.

The Alpine runtime now contains Python 3.14 and FFmpeg 8.1.2. All existing encoder assertions and security integration tests passed on that runtime. All 35 installed runtime Python distributions were compared with the PyPI JSON APIs and matched the latest stable versions at the time of verification, including yt-dlp's supported curl-cffi and EJS dependencies. OS packages continue to come from the pinned Alpine release's supported repositories, with the security refresh marker advanced to this review date.

The changed direct Python packages retain their MIT/BSD-3-Clause licenses. The changed actions and Deno retain MIT/Apache-2.0 licenses. Existing AtomicParsley GPL-2.0 and FFmpeg GPL-enabled packaging remain unchanged in purpose; this update introduces no new license exception. PyPI reports no advisories for the three updated direct Python versions. Trivy 0.74.0 scans of both final and test images found zero HIGH/CRITICAL vulnerabilities, with unfixed findings included. The first test-image scan found advisories in pip tooling; the test stage now removes pip, setuptools, wheel and Alpine py3-pip after installation, matching the final image cleanup. The security tests passed again after this cleanup.

## Verification and rollback

Baseline structural verification passed 439 checks with no failures. After updating pins, the complete CI command `node .ishiku/kit/scripts/verify-app . --full` passed 448 checks with no failures and no unverified requirements. Its required commands passed: compliance, Python compilation, test image build with all 10 security integration tests, Compose validation, and final image build. `actionlint` passed for all workflows.

The amd64 runtime started with a read-only filesystem and dropped capabilities; Uvicorn ran as UID/GID 10001. Readiness, health, initial setup, login and restart with persistent account data passed using isolated synthetic volumes. A baseline image built from the pre-update Git tree successfully read and authenticated against that same synthetic database, and the updated image then successfully reopened it again. No application/data migration is required. For deployment rollback, restore the previous deployed immutable image digest and dependency commit; retain the existing backup procedures in README.md.

The initial local CI verifier reported `VERIFIED`. Release 0.2.2 updates the app version and pinned Compose defaults together. GitHub verification and immutable publication evidence are recorded below after the release completes. No production data is used for validation.
