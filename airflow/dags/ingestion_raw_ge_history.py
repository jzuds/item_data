import os
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta
import logging

default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='ingestion_raw_ge_history',
    default_args=default_args,
    description='collects 5m timeseries data for all items',
    schedule_interval='*/5 * * * *',  # every 5 minutes
    start_date=datetime(2025, 5, 1),
    catchup=False,
    tags=['timeseries', '5m'],
) as dag:

    run_collector = DockerOperator(
        task_id='ingestion_raw_ge_history',
        image='fetch-ge-wiki-prices:latest',
        api_version='auto',
        auto_remove=True,
        command='{{ logical_date.timestamp() | int }}',
        docker_url='unix://var/run/docker.sock',
        network_mode='item_data_network',
        mount_tmp_dir=False,
    )
