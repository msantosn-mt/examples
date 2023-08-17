import psycopg2

#
# Variables
#
psqlHost = '172.17.0.1'
psqlPort = '5432'
psqlUser = 'dbuser'
psqlPwd = 'dbpassword'
psqlDB = 'storage_database'
psqlTable = 'source_data_EUR'

def main(**kwargs):
    data = kwargs['ti'].xcom_pull(task_ids='process_usd_eur_task')
    timestamp = data[0]
    otherCurrenciesValues = data[1]
    print ("otherCurrenciesValues: " + str(otherCurrenciesValues))
    
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
        for currency in otherCurrenciesValues:
            sqlQuery = 'INSERT INTO "' + psqlTable + '" (upload_dt, currency, rate) VALUES (%s,%s,%s)'
            print(sqlQuery, (timestamp, str(currency), otherCurrenciesValues[currency]))
            cursor.execute(sqlQuery, (timestamp, str(currency), str(otherCurrenciesValues[currency])))
        dbsession.commit()
        print("Data inserted")
    except Exception as e:
        print ("Cannot load into the DB: " + str(e))
        exit(1)
    finally:
        # Do not keep DB sessions open - waste of resources
        cursor.close()
        dbsession.close()
