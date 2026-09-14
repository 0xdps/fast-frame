from __future__ import annotations

import re
import shutil
from importlib import resources
from pathlib import Path


class ScaffoldError(ValueError):
    pass


def validate_name(name: str) -> str:
    if not name.isidentifier():
        raise ScaffoldError(f"'{name}' is not a valid Python module name.")
    if name in {"fastframe", "config", "tests"}:
        raise ScaffoldError(f"'{name}' is reserved and cannot be used as an app name.")
    return name


def render_template(text: str, context: dict[str, str]) -> str:
    for key, value in context.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def _template_root() -> Path:
    return Path(str(resources.files("fastframe") / "project_template"))


def _app_template_root() -> Path:
    return _template_root() / "app"


def _migrations_script_mako() -> Path:
    return Path(
        str(
            resources.files("fastframe")
            / "migrations"
            / "templates"
            / "config"
            / "migrations"
            / "script.py.mako"
        )
    )


def _copy_rendered_tree(source: Path, destination: Path, context: dict[str, str]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.rglob("*"):
        if item.is_dir():
            continue
        rel = item.relative_to(source)
        if rel.name.endswith(".tpl"):
            rel = rel.with_name(rel.name[:-4])
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        content = item.read_text(encoding="utf-8")
        target.write_text(render_template(content, context), encoding="utf-8")


def create_project(destination: Path, project_name: str) -> None:
    if destination.exists() and any(destination.iterdir()):
        raise ScaffoldError(f"Destination '{destination}' already exists and is not empty.")
    context = {
        "PROJECT_NAME": project_name,
        "PROJECT_TITLE": project_name.replace("_", " ").title(),
        "APP_CLASS": "Health",
    }
    root = _template_root()
    for item in sorted(root.iterdir()):
        if item.name == "app":
            continue
        target = destination / item.name
        if item.is_dir():
            _copy_rendered_tree(item, target, context)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            text = render_template(item.read_text(encoding="utf-8"), context)
            target.write_text(text, encoding="utf-8")

    migrations_dir = destination / "config" / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_migrations_script_mako(), migrations_dir / "script.py.mako")
    (destination / "health" / "migrations" / "versions").mkdir(parents=True, exist_ok=True)


def create_app(app_dir: Path, app_name: str) -> None:
    if app_dir.exists():
        raise ScaffoldError(f"App directory '{app_dir}' already exists.")
    class_name = app_name.replace("_", " ").title().replace(" ", "")
    context = {
        "APP_NAME": app_name,
        "APP_CLASS": class_name,
    }
    _copy_rendered_tree(_app_template_root(), app_dir, context)
    (app_dir / "migrations" / "versions").mkdir(parents=True, exist_ok=True)


def add_installed_app(settings_path: Path, app_name: str) -> None:
    if not settings_path.is_file():
        return
    content = settings_path.read_text(encoding="utf-8")
    if f'"{app_name}"' in content:
        return
    updated, count = re.subn(
        r"(INSTALLED_APPS = \[\n)",
        rf'\1    "{app_name}",\n',
        content,
        count=1,
    )
    if count:
        settings_path.write_text(updated, encoding="utf-8")


def add_router_to_urls(urls_path: Path, app_name: str) -> None:
    if not urls_path.is_file():
        return
    content = urls_path.read_text(encoding="utf-8")
    if f"{app_name}.urls" in content:
        return
    import_line = f"from {app_name}.urls import router as {app_name}_router\n"
    if "routers = [" not in content:
        return
    content = import_line + content
    content = content.replace(
        "routers = [",
        f"routers = [\n    {app_name}_router,",
        1,
    )
    urls_path.write_text(content, encoding="utf-8")
