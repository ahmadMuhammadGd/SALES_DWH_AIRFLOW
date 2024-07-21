import sys, os 
sys.path.insert(1, os.path.join(os.getcwd()))

from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from common.modules.dwhInterface import dwh_execute_SQL
from common.scripts.mongoInvoices import set_transform_mongo_invoices_view, dwh_stage_unwinded_document

default_args = {
    'owner': 'airflow2',
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

def load():
    dwh_execute_SQL(
        f"""
        USE DWH;
        CALL mongoDB_transformLoad();
        """,
        **mysql_credentials,
        params= None
    )
    
with DAG(
    dag_id="mongodb_pipeline",
    schedule_interval=timedelta(days=1),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["pipeline", "mysql", "mongodb"],
    default_args=default_args
) as dag:
    task_prepare_mongo = PythonOperator(
        task_id = 'task_prepare_mongo',
        python_callable= set_transform_mongo_invoices_view
    )
    
    task_stage = PythonOperator(
        task_id = 'task_stage',
        python_callable=dwh_stage_unwinded_document,
        op_kwargs={
        **mysql_credentials,
        'target_table_name': 'Mongo_Staging'
        },
        dag=dag
    )
    
    task_load = PythonOperator(
        task_id = 'task_load',
        python_callable= load
    )
    
    task_prepare_mongo >> task_stage
    task_stage >> task_load