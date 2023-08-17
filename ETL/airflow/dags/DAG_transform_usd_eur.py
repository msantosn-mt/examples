from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import retrieve_usd_json as retrieve_usd_json_script
import process_usd_eur as process_usd_eur_script
import insert_eur as insert_eur_script

# Define the DAG
dag = DAG(
    dag_id='transform_usd_eur_dag',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None
)

# Define the tasks
retrieve_usd_json_task = PythonOperator(
    task_id='retrieve_usd_json_task',
    python_callable=retrieve_usd_json_script.main,
    dag=dag
)

process_usd_eur_task = PythonOperator(
    task_id='process_usd_eur_task',
    python_callable=process_usd_eur_script.main,
    provide_context=True,
    dag=dag
)

insert_eur_task = PythonOperator(
    task_id='insert_eur_task',
    python_callable=insert_eur_script.main,
    provide_context=True,
    dag=dag
)

# Define the task dependencies
retrieve_usd_json_task >> process_usd_eur_task >> insert_eur_task
