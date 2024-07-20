from os import path

_AIRFLOW_WORKING_DIR = "/opt/airflow"
_MYSQL_CSVS_DIR = "/CLEANED"

_SQL_FILES_PATH = path.join(_AIRFLOW_WORKING_DIR, "SQL_files")
_PATH_SQL_FILE_SCHEME_INIT = path.join(_SQL_FILES_PATH, "dwh-tables-init.sql")
_PATH_SQL_FILE_STAGING = path.join(_SQL_FILES_PATH, "stage_csv.sql")
_PATH_SQL_FILE_TRANSFORM_THEN_LOAD = path.join(_SQL_FILES_PATH, "transform_load.sql")
_PATH_SQL_UPDATE_VIEW = path.join(_SQL_FILES_PATH, "update_view.sql")


_STAGES = path.join(_AIRFLOW_WORKING_DIR, "STAGES")
_LANDED = path.join(_STAGES, "LANDED")
_PROCESSED = path.join(_STAGES, "PROCESSED")
_CLEANED = path.join(_STAGES, "CLEANED")


# Load the SQL files on script import
def load_sql_files():
    global _SQL_TABLES_INIT, _SQL_STAGING, _SQL_TRANSFORM_LOAD, _SQL_UPDATE_VIEW

    with open(_PATH_SQL_FILE_SCHEME_INIT, 'r') as file:
        _SQL_TABLES_INIT = file.read()
    
    with open(_PATH_SQL_FILE_STAGING, 'r') as file:
        _SQL_STAGING = file.read()
    
    with open(_PATH_SQL_FILE_TRANSFORM_THEN_LOAD, 'r') as file:
        _SQL_TRANSFORM_LOAD = file.read()
    
    with open(_PATH_SQL_UPDATE_VIEW, 'r') as file:
        _SQL_UPDATE_VIEW = file.read()
load_sql_files()


