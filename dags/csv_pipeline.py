import sys, os 
sys.path.insert(1, os.path.join(os.getcwd()))

from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from dags.common.global_vars.general_global_var import _LANDED, _PROCESSED, _CLEANED, _MYSQL_CSVS_DIR
from common.modules.airflow_file_handler import Read_landing
from common.modules.dwhInterface import dwh_execute_SQL
from common.scripts.csv_cleaning import CSV_source_cleaner
import shutil
import logging
import json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2021, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

mysql_credentials = {
    "host": "mysql-db",
    "user": "root",
    "password": "root"
}

# Task to stage the cleaned CSV file into the data warehouse
def dwh_stage_task(**kwargs):
    ti = kwargs['ti']
    cleaned_csv_file_path = ti.xcom_pull(key='cleaned_file_name')
    logging.info(f"FILE PATH TO BE STAGED: {cleaned_csv_file_path}")
    
    query = f"""
    USE DWH;
    LOAD DATA INFILE '{cleaned_csv_file_path}'
    INTO TABLE CSV_staging 
    FIELDS TERMINATED BY ',' 
    OPTIONALLY ENCLOSED BY '"' 
    ESCAPED BY '"' 
    LINES TERMINATED BY '\\n' 
    IGNORE 1 LINES;
    """
    
    dwh_execute_SQL(query, **mysql_credentials)

# Task to transform and load data into the data warehouse
def dwh_transform_load_task(**kwargs):
    ti = kwargs['ti']
    source_name = ti.xcom_pull(key='src_file_name')
    
    query = f"USE DWH; CALL CSV_transformLoad('{source_name}');"
    dwh_execute_SQL(query, **mysql_credentials)

# Task to update the views in the data warehouse
def dwh_update_view_task():
    query = "USE DWH; CALL updateViews();"
    dwh_execute_SQL(query, **mysql_credentials)

# Task to check for new CSV files in the landing directory
def check_files(**kwargs):
    reader = Read_landing(_LANDED)
    file_full_path = reader.get_newest_file('.csv')
    
    if not file_full_path:
        return 'task_stop_dag'
    
    file_name = os.path.basename(file_full_path)
    ti = kwargs['ti']
    ti.xcom_push(key='src_file_name', value=file_name)
    ti.xcom_push(key='src_file_path', value=file_full_path)
    return 'task_clean'

def stop_dag(**kwargs):
    logging.info("No files found in the landing directory. Stopping DAG.")

# Task to run the cleaner on the source CSV file
def run_cleaner(**kwargs):
    ti = kwargs['ti']
    file_name = ti.xcom_pull(key='src_file_name')
    source_path = os.path.join(_LANDED, file_name)
    destination_path = os.path.join(_CLEANED, f'cleaned_{file_name}')
    cleaned_file_in_mysql = os.path.join(_MYSQL_CSVS_DIR, os.path.basename(destination_path))
    
    cleaner = CSV_source_cleaner(source_path)
    error_logs = cleaner.cleaner.logger.get_logs()
    cleaner.save_cleaned_data(destination_path)
    
    ti.xcom_push(key='cleaned_file', value=destination_path)
    ti.xcom_push(key='cleaned_file_name', value=cleaned_file_in_mysql)
    ti.xcom_push(key='error_logs', value=error_logs)

def create_error_log_file(**kwargs):
    ti = kwargs['ti']
    src_file_name = os.path.splitext(ti.xcom_pull(key='src_file_name'))[0]
    error_logs = ti.xcom_pull(key="error_logs")
    destination_path = os.path.join(_PROCESSED, f"logs_{src_file_name}.json")
    with open(destination_path, 'w') as f:
        error_logs_string = json.dumps(error_logs, indent=4)
        f.write(error_logs_string)

# Task to move the processed CSV file to the processed directory
def move_processed_file(**kwargs):
    ti = kwargs['ti']
    src_file_name = ti.xcom_pull(key='src_file_name')
    source_path = ti.xcom_pull(key='src_file_path')
    destination_path = os.path.join(_PROCESSED, src_file_name)
    
    shutil.move(source_path, destination_path)


with DAG(
    dag_id="csv_pipeline",
    schedule_interval=timedelta(days=1),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["pipeline", "mysql", "pandas"],
    default_args=default_args
) as dag:
    
    task_check_files = BranchPythonOperator(
        task_id = "task_check_files",
        python_callable = check_files
    )
    
    task_stop_dag = PythonOperator(
        task_id='task_stop_dag',
        python_callable=stop_dag,
        dag=dag,
    )
    
    task_clean = PythonOperator(
        task_id = "task_clean",
        python_callable= run_cleaner
    )
    
    task_create_logs = PythonOperator(
        task_id = 'task_create_error_logs_file',
        python_callable=create_error_log_file
    )
    
    task_stage = PythonOperator(
        task_id = "task_stage",
        python_callable=dwh_stage_task
    )
    
    task_transform_load = PythonOperator(
        task_id = "task_transform_load",
        python_callable=dwh_transform_load_task
    )
    
    task_move_to_processed = PythonOperator(
        task_id="task_move_to_processed",
        python_callable=move_processed_file
    )
    
    task_update_vw = PythonOperator(
        task_id="task_update_vw",
        python_callable=dwh_update_view_task
    )
    
    trigger_rerun = TriggerDagRunOperator(
        task_id='trigger_dag_rerun',
        trigger_dag_id=dag.dag_id)
    
    task_check_files >> [task_clean, task_stop_dag]
    task_stop_dag >> task_update_vw
    task_clean >> [task_create_logs, task_stage]
    task_stage >> task_transform_load
    task_transform_load >> task_move_to_processed
    task_move_to_processed >> trigger_rerun