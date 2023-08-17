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

def main():
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
        sqlQuery = "select upload_dt,api_data ->> 'rates' AS rates from \"" + psqlTable + "\" WHERE api_data IS NOT NULL ORDER BY upload_dt DESC LIMIT 1"
        print("Executing: " + sqlQuery)
        cursor.execute(sqlQuery)
        sqlResults = cursor.fetchall()
        return sqlResults
    except Exception as e:
        print ("Cannot load into the DB: " + str(e))
        exit(1)
    finally:
        # Do not keep DB sessions open - waste of resources
        cursor.close()
        dbsession.close()
