import mysql.connector
import logging
import sqlparse
import re

class Mysql_connector:
    def __init__(self, host:str, user:str, password:str):
        self.host = host
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None
        self.establish_connection()


    def establish_connection(self):
        connection = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
        )
        self.connector_obj = connection
        self.cursor = connection.cursor()
        return connection

    def execute_sql(self, sql_statement: str, params: tuple | list | dict = None):
        statements = sqlparse.split(sql_statement)
        
        for statement in statements:
                statement = sqlparse.format(
                    sql= statement,
                    strip_comments = True,
                )
                logging.info(statement)
                if params and (re.findall('%\(([^)]+)\)s', statement)) or ('%s' in statement):
                    logging.debug('found parameter!')
                    self.cursor.executemany(statement, params)
                else:
                    self.cursor.execute(statement)

        self.connector_obj.commit()

   
    def close_connection(self):
        if self.connector_obj:
            self.cursor.close()
            self.connector_obj.close()