import os, sys
import pandas as pd 
from pathlib import Path
import datetime 
from datetime import timedelta

sys.path.insert(1, os.path.join(os.getcwd()))

from common.dataGenerator.generator import *
from pymongo import MongoClient, UpdateOne
from airflow import DAG
from airflow.operators.python import PythonOperator



def generate_test_csv(dir_path:str =  f'./STAGES/LANDED/')->None:
    # Setting Jeans price to 60 after 2024-01-01 to test Products SCD2 in the DWH
    while True:
        pd_data = CSV_fake(15).df
        pd_data["Date"] = pd.to_datetime(pd_data["Date"])
        filter_condition = (pd_data["Date"] > datetime.datetime(2024, 1, 1)) & (pd_data["Product"] == "Jeans")
        if pd_data[filter_condition].shape[0] > 0:
            break

    pd_data["Unit_price"].loc[filter_condition] = 60.0
    CSVExporter(pd_data)\
        .to_csv(
            f"""{
                os.path.join(
                    dir_path, f"{datetime.datetime.now()}.csv"
                )
            }"""
        )


def generate_test_MongoDB(uri="mongodb://root:example@mongo:27017/")->None:
    json_data = Json_fake(10).data
    db_name = 'transactions'
    collection_name = 'invoices'
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]
    operations = []
    
    for document in json_data:
        username = document['user']['username']
        operation = UpdateOne(
            {'user.username': username},
            {'$set': document},
            upsert=True
        )
        operations.append(operation)

    if operations:
        collection.bulk_write(operations)
    
    return None

    
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.datetime(2021, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}
mysql_credentials = {
    "host": "mysql-db",
    "user": "root",
    "password": "root"
}

with DAG(
    dag_id="generatetestData",
    description="Run this dag to load test data",
    schedule_interval=timedelta(days=1),
    start_date=datetime.datetime(2021, 1, 1),
    catchup=False,
    tags=["dummyDataGeneration", "pandas", "MongoDB"],
    default_args=default_args
) as dag:
    
    generate_csv_task = PythonOperator(
        task_id='generate_csv_task',
        python_callable=generate_test_csv,
        op_kwargs={'dir_path': '/opt/airflow/STAGES/LANDED/'},
    )

    generate_mongo_task = PythonOperator(
        task_id='generate_mongo_task',
        python_callable=generate_test_MongoDB,
        op_kwargs={'uri': 'mongodb://root:example@mongo:27017/'},
    )
    
    generate_csv_task >> generate_mongo_task