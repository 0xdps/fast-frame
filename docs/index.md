# FastFrame

<p align="center">
  <img src="assets/logo.png" alt="FastFrame" width="96" height="96">
</p>

A batteries-included Python web framework built on FastAPI.

Django's developer experience, FastAPI's foundation, and modularity by default. FastFrame does not replace FastAPI or SQLAlchemy. It gives you a project, apps, settings, migrations, a routing facade, and a `manage.py` loop.

Import by area: `fastframe.http`, `fastframe.schemas`, `fastframe.models`. Admin, auth, the token REST API, and Swagger are apps you add to `INSTALLED_APPS`. A new project includes none of them.

## Start here

1. [Tutorial](tutorial.md) — create a project, an app, and a model.
2. [API](api-layer.md) — `fastframe.http.FastFrameAPI`, or a native FastAPI router.
3. [CLI](cli.md) — `fastframe` and `manage.py`.
4. [Settings](settings.md) — what you can configure.

## Build with it

- [Fields](models-fields-design.md) and [queries](orm-features.md)
- [Auth](auth.md) and [permissions](permissions.md)
- [Admin](admin-setup.md), [deploying it](admin-deployment.md), and [security limits](ADMIN_SECURITY_WARNING.md)
- [REST API](rest-api.md) for non-browser clients
- [Background jobs](tasks.md) with Celery

## Reference

- [Apps](app-contract.md)
- [Public API](public-api-v0.1.md)
- [Shell](shell.md)

Design notes, the roadmap, and architecture decision records stay in the [repository](https://github.com/0xdps/fast-frame/tree/trunk/docs). They are not part of this site.
