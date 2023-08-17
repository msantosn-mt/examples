#
# Run:
# $ python <script>
# $ python <script> <currency>
#
import sys
import json, requests
import psycopg2

#
# Variables
#
baseURL = 'https://open.er-api.com/v6/latest/'
currency = 'USD'
psqlHost = '127.0.0.1'
psqlPort = '5432'
psqlUser = 'dbuser'
psqlPwd = 'dbpassword'
psqlDB = 'storage_database'
psqlTable = 'source_data_USD'

#
# Allowing the possibility to include other currencies as source
#
if len(sys.argv) == 2:
    currency = sys.argv[1]
    psqlTable = 'source_data_' + currency


#
# Simple fuinction to get the URL, we have the possibility of 
# catching particular exceptions, like host not responding, network
# errors, etc.
#
def fetch_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Error fetching URL: " + str(e))
        return None

def load_data(data):
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
    finally:
        # Do not keep DB sessions open - waste of resources
        cursor.close()
        dbsession.close()

# Get data from the URL
url = baseURL + currency
data = fetch_url(url)

if data is not None:
    print("Valid JSON response received!\n")
    load_data(data)

else:
    print ("Error")
    # Exiting properly with error code as there was an error with the data.
    exit(1)
