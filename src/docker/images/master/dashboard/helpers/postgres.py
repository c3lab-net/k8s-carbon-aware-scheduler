import psycopg2
import pandas as pd
import os
import pprint
from dotenv import load_dotenv

def get_db_connection(host=None, database=None, autocommit=False):
    print(os.getenv('POSTGRES_HOST'))
    try:
        env_var = os.environ
        load_dotenv()

        conn = psycopg2.connect(host=host if host else os.getenv('POSTGRES_HOST'),
                                database=database if database else os.getenv('POSTGRES_DB'),
                                user=os.getenv('POSTGRES_USER'),
                                password=os.getenv('POSTGRES_PASSWORD'))
        conn.autocommit = autocommit
        return conn
    except Exception as ex:
        raise ValueError("Failed to connect to database.") from ex
    
def psql_execute_list(cursor: psycopg2.extensions.cursor, query: str,
                      fetch_result=False):
    """Execute the psql query and return all rows as a list of tuples."""
    try:
        cursor.execute(query)
        return cursor.fetchall() if fetch_result else cursor.rowcount
    except psycopg2.Error as ex:
        raise ValueError("Failed to execute SQL query.")
    
def postgres_to_dataframe(rows, column_names):
    print(column_names)
    df = pd.DataFrame(data=rows, columns=column_names)
    return df