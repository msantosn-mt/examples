This will deploy all things necessary for an instance of airflow wiht localexecutor. The dags
requester for this assessment are included in the dags directory.

To start:

docker-compose up airflow-init
docker-compose up -d

Then visit the IP of the host, port 8080.
Login with airflow:airflow

You can run these 3 DAGs:
* be_holidays_dag
* currency_rate_dag
* transform_usd_eur_dag
