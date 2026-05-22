from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import the metadata so 'alembic revision --autogenerate' can detect models.
from app.core.config import settings  # noqa: E402 · routes DATABASE_URL through the canonical normalizer
from app.db.base import Base  # noqa: F401
from app.models import *  # noqa: F401,F403  ← register all models on Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Always use Settings.database_url · this routes through the pydantic
# field_validator that normalises `postgres://` and `postgresql://` (Fly /
# Heroku style) into the SQLAlchemy + psycopg3 dialect form
# `postgresql+psycopg://...`. Without this, alembic falls back to the legacy
# psycopg2 driver and crashes with ModuleNotFoundError on hosts where only
# psycopg3 is installed (which is our prod container).
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
