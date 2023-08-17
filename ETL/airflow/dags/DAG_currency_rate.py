from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import fetch_url as fetch_url_script
import insert_currency_rate as insert_currency_rate_script

#
# Variables
#
url = 'https://open.er-api.com/v6/latest/USD'

# Define the DAG
dag = DAG(
    dag_id='currency_rate_USD',
    start_date=datetime(2023, 1, 1),
    schedule_interval="@daily"
)

# Define the tasks
fetch_url_task = PythonOperator(
    task_id='fetch_url_task',
    python_callable=fetch_url_script.fetch_url,
    op_args=[url],
    dag=dag
)

insert_currency_rate_task = PythonOperator(
    task_id='insert_currency_rate_task',
    python_callable=insert_currency_rate_script.load_data,
    provide_context=True,
    dag=dag
)

# Define the task dependencies
fetch_url_task >> insert_currency_rate_task

