import json
import psycopg2

#
# Variables
#
psqlHost = '172.17.0.1'
psqlPort = '5432'
psqlUser = 'dbuser'
psqlPwd = 'dbpassword'
psqlDB = 'storage_database'
psqlTable = 'source_data_USD'

def load_data(**kwargs):
    data = kwargs['ti'].xcom_pull(task_ids='fetch_url_task')
    try:
        dbsession = psycopg2.connect(
            host=psqlHost,
            port=psqlPort,
            user=psqlUser,
            password=psqlPwd,
            database=psqlDB
        )
        cursor = dbsession.cursor()
        # Insert into the DB
        sqlQuery = 'INSERT INTO "' + psqlTable + '" (upload_dt, api_data) VALUES (NOW(), %s)'
        cursor.execute(sqlQuery, (json.dumps(data),))
        dbsession.commit()
        print("Data inserted")
    except Exception as e:
        print ("Cannot load into the DB: " + str(e))
        exit(1)
    finally:
        # Do not keep DB sessions open - waste of resources
        cursor.close()
        dbsession.close()
