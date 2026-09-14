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


def run_migrations_offline() -> None:
    registry, target_metadata = _prepare_metadata()
    url = config.get_main_option("sqlalchemy.url")
    version_locations = [str(p) for p in get_version_locations(registry, None)]

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_locations=version_locations,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    registry, target_metadata = _prepare_metadata()
    version_locations = [str(p) for p in get_version_locations(registry, None)]
    connectable = get_engine(None)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_locations=version_locations,
        )

        with context.begin_transaction():
            context.run_migrations()


def run_alembic_env() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
