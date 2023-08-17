import sys
import json, requests

#defaultUrl = 'https://openholidaysapi.org/PublicHolidays?countryIsoCode=BE&languageIsoCode=EN&validFrom=2023-01-01&validTo=2023-12-31'

def fetch_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Error fetching URL: " + str(e))
        return None
