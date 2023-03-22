#!/usr/bin/env python3

import psycopg2
import logging
import traceback
from typing import Sequence, Any, Union

from util import get_env_var

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
        logging.error(f'psql_execute_scalar("{query}", {args}): {ex}')
        logging.error(traceback.format_exc())
        raise ValueError("Failed to execute SQL query.")
    return result[0] if result is not None else None


def psql_execute_list(cursor: psycopg2.extensions.cursor, query: str,
                      args: Union[Sequence[Any], dict[str, str]] = None, fetch_result=False) -> list[tuple]:
    """Execute the psql query and return all rows as a list of tuples."""
    try:
        cursor.execute(query, args)
        return cursor.fetchall() if fetch_result else cursor.rowcount
    except psycopg2.Error as ex:
        logging.error(f'psql_execute_scalar("{query}", {args}): {ex}')
        logging.error(traceback.format_exc())
        raise ValueError("Failed to execute SQL query.")

