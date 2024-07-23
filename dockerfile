FROM apache/airflow:2.9.0

COPY requirements.txt .

RUN python3 -m pip install --upgrade pip \
&& pip install -r requirements.txt

COPY ./airflow.cfg /opt/airflow/airflow.cfg

USER root
COPY setup.sh /opt/airflow/setup.sh
RUN chmod +x /opt/airflow/setup.sh

USER airflow
RUN /opt/airflow/setup.sh