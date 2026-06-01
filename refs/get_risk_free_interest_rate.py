import requests

# URL to fetch the latest interest rate
url = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
       "v2/accounting/od/avg_interest_rates?sort=-record_date&format=json&page[number]=1&page[size]=1")

# Send a GET request to the API
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Check if the data key exists and contains records
    if data.get("data") and len(data["data"]) > 0:
        latest_record = data["data"][0]
        interest_rate = latest_record.get("avg_interest_rate_amt")
        record_date = latest_record.get("record_date")
        
        print(f"Latest Risk Free Interest Rate on {record_date}: {interest_rate}%")
    else:
        print("No data available in the response.")
else:
    print(f"Failed to fetch data. HTTP Status code: {response.status_code}")