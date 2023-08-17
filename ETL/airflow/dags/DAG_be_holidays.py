from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import fetch_url as fetch_url_script
import insert_holidays as insert_holidays_script

#
# Variables
#
url = 'https://openholidaysapi.org/PublicHolidays?countryIsoCode=BE&languageIsoCode=EN&validFrom=2023-01-01&validTo=2023-12-31'

# Define the DAG
dag = DAG(
    dag_id='be_holidays',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None
)

# Define the tasks
fetch_url_task = PythonOperator(
    task_id='fetch_url_task',
    python_callable=fetch_url_script.fetch_url,
    op_args=[url],
    dag=dag
)

insert_holidays_task = PythonOperator(
    task_id='insert_holidays_task',
    python_callable=insert_holidays_script.process_json,
    provide_context=True,
    dag=dag
)

# Define the task dependencies
fetch_url_task >> insert_holidays_task

