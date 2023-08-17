Excercises:

* Holidays data
  - Reads list of Belgium holidays from API https://openholidaysapi.org/PublicHolidays?countryIsoCode=BE&languageIsoCode=EN&validFrom=2023-01-01&validTo=2023-12-31
  - Documentation - https://www.openholidaysapi.org/en/
  - Loads data to a table be_holidays on the storage database.

* Currency Rate Data
  - Reads a Currency Rate from the API https://open.er-api.com/v6/latest/USD
  - Documentation - https://www.exchangerate-api.com/docs/free
  - Loads Data in JSON format to a table source_data_USD on the storage database tagged with the  collection timestamp to upload_dt field.

* Data Transformation
  - Transform / Clean
  - Data is coming with USD base, to convert this to EUR base and store with a precision of 4 decimal places to source_data_EUR table.
  - Build a view named exchange_rates with a union all of data from the source_data_USD and data from the source_data_EUR while joining
    this data to the be_holidays table indicating holidays with description.


Directories:

* airflow - Airflow infrastructure and DAGs
* external-db - Volatile database to store data not directly related to airflow

