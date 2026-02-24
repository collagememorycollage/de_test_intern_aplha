
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.models import Variable
from datetime import datetime, timedelta
import random

default_args = {
    'owner': 'data_eng',
    'start_date': datetime(2023, 1, 1),
    'depends_on_past': True,
    'retries': 5,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'order_processing_extended',
    default_args=default_args,
    schedule_interval='@hourly',
    catchup=True,
    tags=['orders'],
    max_active_runs=5
)

def extract_orders(**kwargs):
    print("Extracting orders...")
    if random.random() < 0.2:
        raise Exception("Random extraction failure")  # нестабильность

def transform_orders(**kwargs):
    print("Transforming orders...")

def load_orders(**kwargs):
    print("Loading orders to warehouse...")

def notify_failure(context):
    print("Sending alert to Slack...")  # но не интегрирован

start = DummyOperator(task_id='start', dag=dag)

extract = PythonOperator(
    task_id='extract_orders',
    python_callable=extract_orders,
    provide_context=True,
    dag=dag,
)

transform = PythonOperator(
    task_id='transform_orders',
    python_callable=transform_orders,
    provide_context=True,
    dag=dag,
)

load = PythonOperator(
    task_id='load_orders',
    python_callable=load_orders,
    provide_context=True,
    dag=dag,
)

check_not_empty = PostgresOperator(
    task_id='check_agg_table',
    postgres_conn_id='postgres_default',
    sql='SELECT COUNT(*) FROM orders_agg;',
    dag=dag,
)

end = DummyOperator(task_id='end', dag=dag)

start >> extract >> transform >> load >> check_not_empty >> end
