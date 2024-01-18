from __future__ import annotations
from math import log
import os
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database
from sqlalchemy import (
    create_engine,
    text,
)
from sqlalchemy.schema import CreateSchema

from src.logging.service import logger
from src.config import (
    IN_MAINTENANCE,
    DATABASE_HOST,
    DATABASE_NAME,
    DATABASE_URL_SYNC,
    DATABASE_URL_ASYNC,
    SHARED_SCHEMA_NAME,
    TENANT_SCHEMA_NAME,
)


# TODO: Proper singleton
class DatabaseService:
    _instance = None

    @classmethod
    @lru_cache(maxsize=1)
    def get(cls) -> DatabaseService:
        if cls._instance is None:
            cls._instance = DatabaseService()
        return cls._instance

    def __init__(self) -> None:
        __class__.create_db()
        self._async_engine: AsyncEngine = create_async_engine(
            DATABASE_URL_ASYNC,
            future=True,
            echo=True,
            # pool_size=50,
        )

        self._async_session_maker: AsyncSession = sessionmaker(
            self._async_engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    @classmethod
    def get_schema_context(cls, schema_name: str = SHARED_SCHEMA_NAME) -> None:
        options = {}
        if schema_name == SHARED_SCHEMA_NAME:
            options['schema_translate_map'] = { 'tenant': None }
        else:
            options['schema_translate_map'] = { 'tenant': schema_name, 'shared': None }
        return options

    @classmethod
    @asynccontextmanager
    async def async_session(cls, schema_name: str = SHARED_SCHEMA_NAME) -> AsyncSession:
        """Async Context Manager to create a session with a specific schema context that auto commits.
        Will lazy init db service if not already done.

        Args:
            schema_name (str): Database Schema Name for use with e.g. 'SELECT * FROM {schema_name}.some_table'

        Returns:
            AsyncSession: Async Session with the schema context set.

        Yields:
            Iterator[AsyncSession]: Async Session with the schema context set.
        """
        if IN_MAINTENANCE:
            logger.error("Request received during maintenance window.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is currently under maintenance."
            )

        # Handle tenant switch
        session = cls.get()._async_session_maker()
        await session.connection(execution_options=cls.get_schema_context(schema_name))

        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

    @classmethod
    def create_db(cls):
        if not database_exists(url=DATABASE_URL_SYNC):
            logger.warning(f"Creating database: {DATABASE_NAME}...")
            create_database(url=DATABASE_URL_SYNC)
            logger.warning('Creating default schemas...')
            cls.create_schema(SHARED_SCHEMA_NAME)
            cls.create_schema(TENANT_SCHEMA_NAME)
            logger.warning('Default schemas created.')
            logger.warning('Running migrations as database was just created...')
            cls.run_migrations()

            # TODO: Add some more detailed error handling if this borks
            if not database_exists(url=DATABASE_URL_SYNC):
                raise Exception('COULD NOT CREATE DATABASE!')
            else:
                logger.warning('Database created.')
        else:
            logger.info(f"Database '{DATABASE_HOST}/{DATABASE_NAME}' already exists. Nothing to do.")

    @classmethod
    def create_schema(cls, schema_name: str) -> None:
        """
        Creates a new blank schema with the provided name, which can then be accessed as e.g.

        ```
        select * from 'schema_name'.some_table
        ```

        Args:
            schema_name (str): Schema name
        """
        sync_engine = create_engine(DATABASE_URL_SYNC)
        with sync_engine.begin() as conn:
            if not conn.dialect.has_schema(conn, schema_name):
                logger.warning(f"Creating schema: '{schema_name}'...")
                conn.execute(CreateSchema(schema_name))
                if not conn.dialect.has_schema(conn, schema_name):
                    logger.error(f"Could not create schema: '{schema_name}'.")
            else:
                logger.info(f"Schema '{schema_name}' already exists.")

        sync_engine.dispose()

    @classmethod
    def clone_db_schema(cls, source_schema_name: str, target_schema_name: str) -> None:
        """
        Clones the table definitions from one schema to another.
        If a table already exists in the target_schema, it will skip it.
        Does not clone any data. Idempotent.

        Args:
            source_schema_name (str): Schema to clone
            target_schema_name (str): Schema to clone into. Must exist already.
        """
        sync_engine = create_engine(DATABASE_URL_SYNC)
        with sync_engine.begin() as conn:
            logger.warning(f"Cloning schema '{source_schema_name}' to '{target_schema_name}...")

            # Get all tables in schema
            sql_schema_tables = "select * from information_schema.tables where table_schema = 'tenant'"
            schema_tables = [r['table_name'] for r in conn.execute(text(sql_schema_tables)).mappings().all()]

            # Clone tables one for one
            for table_name in schema_tables:
                logger.warning(f"Cloning {source_schema_name}.{table_name} to {target_schema_name}.{table_name}...")
                sql_clone = f"create table if not exists {target_schema_name}.{table_name} (like {source_schema_name}.{table_name} including all)"
                clone_res = conn.execute(text(sql_clone))

        logger.warning("Schema cloned.")
        sync_engine.dispose()

    # TODO: Do properly online with alembic
    @classmethod
    def run_migrations(cls):
        os.system('alembic upgrade head')

    @classmethod
    def drop_db(cls):
        if database_exists(url=DATABASE_URL_SYNC):
            logger.warning(f"Dropping database: {DATABASE_NAME}...")
            drop_database(url=DATABASE_URL_SYNC)

    @classmethod
    async def shutdown(cls):
        if cls._instance is not None:
            if cls._instance._async_session_maker is not None:
                await cls._instance._async_session_maker.close_all()
            if cls._instance._async_engine is not None:
                await cls._instance._async_engine.dispose()
