#!/usr/bin/env python3

import psycopg2
import psycopg2.extras
import logging
import traceback
from typing import Sequence, Any, Union
from flask import current_app

from api.util import get_env_var

def get_db_connection(host=None, database=None):
    try:
        conn = psycopg2.connect(host=host if host else get_env_var('POSTGRES_HOST'),
                                database=database if database else get_env_var('POSTGRES_DB'),
                                user=get_env_var('POSTGRES_USER'),
                                password=get_env_var('POSTGRES_PASSWORD'))
        return conn
    except Exception as ex:
        raise ValueError("Failed to connect to database.") from ex

def psql_execute_scalar(cursor: psycopg2.extensions.cursor, query: str, args: Sequence[Any] = None) -> Any | None:
    """Execute the psql query and return the first column of first row."""
    try:
        cursor.execute(query, args)
        result = cursor.fetchone()
    except psycopg2.Error as ex:
        current_app.logger.error(f'psql_execute_scalar("{query}", {args}): {ex}')
        current_app.logger.error(traceback.format_exc())
        raise ValueError("Failed to execute SQL query.")
    return result[0] if result is not None else None


def psql_execute_list(cursor: psycopg2.extensions.cursor, query: str,
                      args: Union[Sequence[Any], dict[str, str]] = None) -> list[tuple]:
    """Execute the psql query and return all rows as a list of tuples."""
    try:
        cursor.execute(query, args)
        result = cursor.fetchall()
    except psycopg2.Error as ex:
        current_app.logger.error(f'psql_execute_scalar("{query}", {args}): {ex}')
        current_app.logger.error(traceback.format_exc())
        raise ValueError("Failed to execute SQL query.")
    return result

def psql_execute_values(cursor: psycopg2.extensions.cursor, query: str,
                      args: Sequence[Any] = None) -> list[tuple]:
    """Execute the psql query and return all rows as a list of tuples."""
    try:
        psycopg2.extras.execute_values(cursor, query, args)
        return cursor.rowcount
    except psycopg2.Error as ex:
        current_app.logger.error(f'psql_execute_values("{query}", {args}): {ex}')
        current_app.logger.error(traceback.format_exc())
        raise ValueError("Failed to execute SQL query.")

psycopg2.extras.register_uuid()
