#
# Run:
# $ python <script>
# $ python <script> <url>
#
import sys
import json, requests
import psycopg2

#
# Variables
#
defaultUrl = 'https://openholidaysapi.org/PublicHolidays?countryIsoCode=BE&languageIsoCode=EN&validFrom=2023-01-01&validTo=2023-12-31'
psqlHost = '127.0.0.1'
psqlPort = '5432'
psqlUser = 'dbuser'
psqlPwd = 'dbpassword'
psqlDB = 'storage_database'

#
# Trying to not hardcode these variables unless is really necessary.
# We allow the script to receive a URL at runtime.
#
if len(sys.argv) == 2:
    url = sys.argv[1]
else:
    url = defaultUrl


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

#
# This function will receive a JSON variable that will be iterated over
# and insert into a DB only the fields that are important to us.
#
def process_json(data):
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
            sqlQuery = "INSERT INTO be_holidays (id, event_date, holiday_description) VALUES (%s, %s, %s)"
            print(sqlQuery, (entry_id, entry_timestamp, entry_description))
            cursor.execute(sqlQuery, (entry_id, entry_timestamp, entry_description))
        dbsession.commit()
        print("Data inserted")
    except Exception as e:
        print ("Cannot load into the DB: " + str(e))
    finally:
        # Do not keep DB sessions open - waste of resources
        cursor.close()
        dbsession.close()

# Get data from the URL
data = fetch_url(url)

if data is not None:
    print("Valid JSON response received!\n")
    process_json(data)

else:
    print ("Error")
    # Exiting properly with error code as there was an error with the data.
    exit(1)
