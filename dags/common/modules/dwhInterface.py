from contextlib import contextmanager
from common.modules.mysql_handler import Mysql_connector

@contextmanager
def mysql_connection(host: str, user: str, password: str):
    connector = Mysql_connector(host=host, user=user, password=password)
    try:
        yield connector
    finally:
        connector.close_connection()

def dwh_execute_SQL(sql:str, host: str, user: str, password: str, params=None):
    with mysql_connection(host, user, password) as handler:
        handler.execute_sql(sql, params)

if '__name__' == 'main':
    pass