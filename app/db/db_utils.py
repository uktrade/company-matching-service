import logging

import sqlalchemy

from app.db.models import sql_alchemy


def execute_query(query, raise_if_fail=True):
    result_set = execute_statement(query, None, raise_if_fail)
    rows = result_set.fetchall()
    return rows


def execute_statement(stmt, data=None, raise_if_fail=True):
    connection = sql_alchemy.engine.connect()
    transaction = connection.begin()
    try:
        status = connection.execute(stmt, data)
        transaction.commit()
        connection.close()
        return status
    except sqlalchemy.exc.ProgrammingError as err:
        transaction.rollback()
        logging.error(f'db error: {str(err)}')
        if raise_if_fail:
            raise err
        connection.close()


def table_exists(schema, table_name, materialized_view=False):
    query = f"""
     SELECT EXISTS (
        SELECT 1
           FROM   {'information_schema.tables' if not materialized_view else 'pg_matviews'}
           WHERE  {'table_schema' if not materialized_view else 'schemaname'} = '{schema}'
           AND    {'table_name' if not materialized_view else 'matviewname'} = '{table_name}'
     );
    """
    return list(execute_statement(query))[0][0]
