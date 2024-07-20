FROM apache/airflow:2.9.0
COPY requirements.txt .

# USER root
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

# USER airflow

COPY ./airflow.cfg /opt/airflow/airflow.cfg