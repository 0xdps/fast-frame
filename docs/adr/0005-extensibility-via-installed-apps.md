# ADR 0005: Extensibility via installed apps

## Status

Accepted

## Addition (2026-10-04)

The consequence below that leaves storage backends "deferred until needed" is withdrawn. FastFrame will not ship an email battery or a storage battery. Background jobs are the optional `fastframe.tasks` app. See [ADR 0012](0012-background-jobs.md). The rest of this decision is unchanged.

## Addition (2026-10-06)

The consequence that defers cache backends is decided in [ADR 0013](0013-caching.md): one cache, Redis by default, and an in-process backend for tests. That is not a general backend protocol. Storage backends stay withdrawn.

## Context

FastFrame aims for “batteries included, not forced.” Django's extensibility model (installed apps, AppConfig, commands) is a proven pattern; cloning every Django feature is not.

## Decision

- Projects configure **`INSTALLED_APPS`**.
- Apps may contribute **`AppConfig.ready()`**, **models**, **routers**, and **management commands** via documented conventions (see [docs/app-contract.md](../app-contract.md)).
- Features like admin, auth, and templates should ship as **optional apps** when ready, not as mandatory core.

## Consequences

- v0.1 must implement a minimal but stable app registry and discovery.
- Third-party packages can target the same contract as first-party apps.
- Full “backend” protocols (storage, cache, auth backends) are deferred until needed.
