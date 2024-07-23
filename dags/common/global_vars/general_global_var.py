import os
from os import path

# _AIRFLOW_WORKING_DIR = "/home/ahmad/repo/SALES_DWH_AIRFLOW"
_AIRFLOW_WORKING_DIR = "/opt/airflow"
_MYSQL_CSVS_DIR = "/CLEANED"

_STAGES = path.join(_AIRFLOW_WORKING_DIR, "STAGES")
_LANDED = path.join(_STAGES, "LANDED")
_PROCESSED = path.join(_STAGES, "PROCESSED")
_CLEANED = path.join(_STAGES, "CLEANED")

_SQL_DIR = path.join(_AIRFLOW_WORKING_DIR, "dwh-SQL")