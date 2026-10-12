
"""PostgreSQL connection utilities for the SDM pipeline."""

import psycopg2
from psycopg2 import sql
from sqlalchemy import URL, create_engine, inspect
from sqlalchemy.orm import sessionmaker

from src.utils.db_config import resolve_db_config


def pg_client(config: dict | None = None):
    """Create SQLAlchemy resources for the SDM pipeline.

    Returns:
        engine, connection, session, inspector

    The caller owns these resources and must close them.
    """
    settings = resolve_db_config(config)

    url = URL.create(
        "postgresql+psycopg2",
        username=settings["user"],
        password=settings["password"],
        host=settings["host"],
        port=settings["port"],
        database=settings["database"],
    )

    # PostgreSQL search_path is an identifier setting, not a SQL
    # value parameter. Validate it before including it in options.
    schema = settings["schema"]

    if not isinstance(schema, str) or not schema.isidentifier():
        raise ValueError("Invalid PostgreSQL schema name")

    engine = create_engine(
        url,
        connect_args={
            "options": f"-csearch_path={schema}",
        },
        pool_pre_ping=True,
        pool_recycle=1800,
    )

    connection = None
    session = None

    try:
        connection = engine.connect()
        Session = sessionmaker(bind=engine)
        session = Session()
        inspector = inspect(engine)

        return engine, connection, session, inspector

    except Exception:
        if session is not None:
            session.close()
        if connection is not None:
            connection.close()
        engine.dispose()
        raise


def pg_cursor(config: dict | None = None):
    """Create a psycopg2 connection and cursor."""
    settings = resolve_db_config(config)

    connection = psycopg2.connect(
        host=settings["host"],
        database=settings["database"],
        port=settings["port"],
        user=settings["user"],
        password=settings["password"],
        connect_timeout=10,
    )

    try:
        cursor = connection.cursor()
        return connection, cursor
    except Exception:
        connection.close()
        raise