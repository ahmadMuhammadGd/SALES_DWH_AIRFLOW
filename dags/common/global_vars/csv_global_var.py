from os import path

_AIRFLOW_WORKING_DIR = "./"
# _AIRFLOW_WORKING_DIR = "/opt/airflow"
_MYSQL_CSVS_DIR = "/CLEANED"

_STAGES = path.join(_AIRFLOW_WORKING_DIR, "STAGES")
_LANDED = path.join(_STAGES, "LANDED")
_PROCESSED = path.join(_STAGES, "PROCESSED")
_CLEANED = path.join(_STAGES, "CLEANED")


