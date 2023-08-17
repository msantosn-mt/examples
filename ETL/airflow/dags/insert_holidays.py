import json
import psycopg2

psqlHost = '172.17.0.1'
psqlPort = '5432'
psqlUser = 'dbuser'
psqlPwd = 'dbpassword'
psqlDB = 'storage_database'
psqlTable = 'be_holidays'

#
# This function will receive a JSON variable that will be iterated over
# and insert into a DB only the fields that are important to us.
#

def process_json(**kwargs):
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
        # Iterate through JSON
        for json_entry in data:
            entry_id = json_entry['id']
            entry_timestamp = json_entry['startDate']
            entry_description_node = json_entry['name']
            entry_description = entry_description_node[0]['text']
            sqlQuery = "INSERT INTO " + psqlTable + " (id, event_date, holiday_description) VALUES (%s, %s, %s)"
            print(sqlQuery, (entry_id, entry_timestamp, entry_description))
            cursor.execute(sqlQuery, (entry_id, entry_timestamp, entry_description))
        dbsession.commit()
        print("Data inserted")
    except Exception as e:
        print ("Cannot load into the DB: " + str(e))
        exit(1)
    finally:
        # Do not keep DB sessions open - waste of resources
        cursor.close()
        dbsession.close()
