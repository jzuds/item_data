import os
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='5m_timeseries_blood_runes_collector',
    default_args=default_args,
    description='Run blood runes data collector',
    schedule_interval='*/5 * * * *',  # every 5 minutes
    start_date=datetime(2025, 5, 31),
    catchup=False,
    tags=['timeseries', '5m'],
) as dag:

    run_collector = DockerOperator(
        task_id='collect_oak_planks',
        image='data_collector:latest',
        api_version='auto',
        auto_remove=True,
        command='--item 565',
        docker_url='unix://var/run/docker.sock',
        network_mode='item_data_item_data_network',
        environment={
            'DB_HOST': os.getenv("DB_HOST", "postgres"),
            'DB_NAME': os.getenv("DB_NAME", "item_data_db"),
            'DB_USER': os.getenv("DB_USER", "item_data_user"),
            'DB_PASSWORD': os.getenv("DB_PASSWORD", "secure_password_123"),
        },
        mount_tmp_dir=False,
    )
