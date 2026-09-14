# Vision & thesis

FastFrame is a **batteries-included Python web framework built on FastAPI**.

## Goal

Provide a **Django-like developer experience** from initial development through production, while using **FastAPI** as the HTTP/ASGI foundation.

We are **not** recreating Django feature-for-feature. FastFrame should provide:

- Strong conventions
- Sensible defaults
- A cohesive development workflow
- Composition of mature Python libraries underneath

## Core thesis

> **Django's developer experience, FastAPI's foundation, and modularity by default.**

## Positioning

**Do not** position FastFrame as “a Django replacement.”

**Do** position it as:

- FastFrame — A batteries-included Python web framework built on FastAPI.
- Django's developer experience, FastAPI's foundation.
- FastAPI with batteries included.

The strongest long-term positioning is **developer experience and conventions**, not the underlying technology list.

## Core question

Can we give Python developers the **simplicity and completeness of Django's project workflow** while keeping **FastAPI as the HTTP layer**?

If yes, Django-like functionality can be added incrementally without bloating the initial product.

## What “high-level experience first” means

- **Workflow familiarity:** `manage.py`, apps, settings, migrations, shell.
- **Thin data helpers:** simple calls such as `filter`, `first`, `get`, `save`, `create`, `delete`, `count`.
- **Honest escape hatch:** complex queries and advanced ORM usage use **SQLAlchemy** directly.
- **HTTP stays FastAPI:** no Django views; routers, dependencies, and Pydantic as-is.
- **Extensibility:** installable apps and hooks (Django's advanced lesson), not a monolithic clone of every Django subsystem.

## MVP success (v0.1)

A developer can:

1. Create a project and run the dev server immediately (zero-decision start).
2. Create an app and define a model.
3. Generate and apply migrations without manual Alembic setup.
4. Explore models in an initialized shell.
5. Write and run tests with the app bootstrapped.
6. Deploy via conventional ASGI (Uvicorn, etc.) without framework-specific hosting.
7. Understand project layout without reading extensive architecture docs.

The first milestone is **a coherent development loop**, not feature completeness.
