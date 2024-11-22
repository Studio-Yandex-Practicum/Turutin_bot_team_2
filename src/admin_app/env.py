from __future__ import with_statement

import logging
from logging.config import fileConfig
from typing import List

from alembic import context
from alembic.migration import MigrationContext
from alembic.script import Script
from flask import current_app

from models import Base

config = context.config

fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

target_metadata = Base.metadata

config.set_main_option(
    'sqlalchemy.url',
    str(
        current_app.extensions['migrate'].db.get_engine().url,
    ).replace('%', '%%'),
)


def run_migrations_offline() -> None:
    """Запускаем миграции в оффлайн-режиме."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запускаем миграции в онлайн-режиме."""
    def process_revision_directives(
            context: MigrationContext, revision: str, directives: List[Script],
    ) -> None:
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('Нет изменений в схеме.')

    connectable = current_app.extensions['migrate'].db.get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
            **current_app.extensions['migrate'].configure_args,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
