#!/usr/bin/env python3

import psycopg2
import psycopg2.extras
import logging
import traceback
from typing import Sequence, Any, Union

from util import get_env_var

Json = psycopg2.extras.Json

def get_db_connection(host=None, database=None, autocommit=False):
    try:
        conn = psycopg2.connect(host=host if host else get_env_var('POSTGRES_HOST'),
                                database=database if database else get_env_var('POSTGRES_DB'),
                                user=get_env_var('POSTGRES_USER'),
                                password=get_env_var('POSTGRES_PASSWORD'))
        conn.autocommit = autocommit
        return conn
    except Exception as ex:
        raise ValueError("Failed to connect to database.") from ex

def psql_execute_scalar(cursor: psycopg2.extensions.cursor, query: str, args: Sequence[Any] = None) -> Any | None:
    """Execute the psql query and return the first column of first row."""
    try:
        cursor.execute(query, args)
        result = cursor.fetchone()
    except psycopg2.Error as ex:
        raise ValueError(f"Failed to execute SQL query: {ex}") from ex
    return result[0] if result is not None else None


def psql_execute_list(cursor: psycopg2.extensions.cursor, query: str,
                      args: Union[Sequence[Any], dict[str, str]] = None, fetch_result=False) -> list[tuple]:
    """Execute the psql query and return all rows as a list of tuples."""
    try:
        cursor.execute(query, args)
        return cursor.fetchall() if fetch_result else cursor.rowcount
    except psycopg2.Error as ex:
        raise ValueError(f"Failed to execute SQL query: {ex}") from ex

