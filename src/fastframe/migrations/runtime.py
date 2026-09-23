from __future__ import annotations

from logging.config import fileConfig

from alembic import context

from fastframe.core.bootstrap import bootstrap, get_apps_registry
from fastframe.db.engine import get_engine
from fastframe.db.init import import_app_models
from fastframe.migrations.paths import get_version_locations
from fastframe.models.base import Model

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _prepare_metadata():
    bootstrap(None)
    registry = get_apps_registry()
    import_app_models(registry)
    return registry, Model.metadata


def _get_app_table_names(registry) -> set[str]:
    """Collect table names for models defined in installed apps only.

    Model.metadata is process-global, so in tests (or long-lived processes)
    it accumulates tables from unrelated models. Migrations must only track
    tables owned by the project's installed apps.
    """
    import sys

    from fastframe.models.base import Model, ModelMeta

    tables: set[str] = set()
    for app_config in registry.app_configs:
        models_module = sys.modules.get(f"{app_config.name}.models")
        if models_module is None:
            continue
        for attr_name in dir(models_module):
            attr = getattr(models_module, attr_name)
            if (
                isinstance(attr, ModelMeta)
                and issubclass(attr, Model)
                and attr is not Model
                and hasattr(attr, "__tablename__")
            ):
                tables.add(attr.__tablename__)
    return tables


def _include_app_objects_factory(allowed_tables: set[str]):
    """Alembic include_object hook: only allow installed apps' tables."""

    def include_object(obj, name, type_, reflected, compare_to):
        if type_ == "table":
            return name in allowed_tables
        table = getattr(obj, "table", None)
        if table is not None:
            return table.name in allowed_tables
        return True

    return include_object


def run_migrations_offline() -> None:
    registry, target_metadata = _prepare_metadata()
    url = config.get_main_option("sqlalchemy.url")
    version_locations = [str(p) for p in get_version_locations(registry, None)]
    include_object = _include_app_objects_factory(_get_app_table_names(registry))

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_locations=version_locations,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    registry, target_metadata = _prepare_metadata()
    version_locations = [str(p) for p in get_version_locations(registry, None)]
    include_object = _include_app_objects_factory(_get_app_table_names(registry))
    connectable = get_engine(None)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_locations=version_locations,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


def run_alembic_env() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
