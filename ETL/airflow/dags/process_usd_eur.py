import json

# New BaseCurrency
baseCurrency = 'EUR'

def extract_value(json_data, key):
    data = json.loads(json_data)
    return data.get(key)

def main(**kwargs):
    sqlResults = kwargs['ti'].xcom_pull(task_ids='retrieve_usd_json_task')

    # We should have only one row as results.
    if len(sqlResults) != 1:
        print("Error, the object has more than one result or no results")
        exit(1)

    # Unpack the results
    for row in sqlResults:
        upload_timestamp = str(row[0])
        json_data = row[1]

    # Get baseCurrency value
    baseCurrencyValue = extract_value(json_data, baseCurrency)
    print ("baseCurrencyValue: " + str(baseCurrencyValue))

    # Initialize Dict
    otherCurrenciesValues = dict.fromkeys(json.loads(json_data))

    # Populate Dict by Iterating through it and finding the value, then dividing the new basevalue by the value from the reference currency.
    for key in otherCurrenciesValues:
        otherCurrencyValueInUSD = extract_value(json_data, key)
        otherCurrenciesValues[key] = round((baseCurrencyValue / float(otherCurrencyValueInUSD)), 4)
        print("Key: " + str(key) + ", Value: " + str(otherCurrenciesValues[key]))

    # Printing just to make sure everything looks good.
    print(otherCurrenciesValues)

    return (upload_timestamp,otherCurrenciesValues)
