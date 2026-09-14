# ADR 0005: Extensibility via installed apps

## Status

Accepted

## Context

FastFrame aims for “batteries included, not forced.” Django's extensibility model (installed apps, AppConfig, commands) is a proven pattern; cloning every Django feature is not.

## Decision

- Projects configure **`INSTALLED_APPS`**.
- Apps may contribute **`AppConfig.ready()`**, **models**, **routers**, and **management commands** via documented conventions (see [docs/app-contract.md](../docs/app-contract.md)).
- Features like admin, auth, and templates should ship as **optional apps** when ready, not as mandatory core.

## Consequences

- v0.1 must implement a minimal but stable app registry and discovery.
- Third-party packages can target the same contract as first-party apps.
- Full “backend” protocols (storage, cache, auth backends) are deferred until needed.
