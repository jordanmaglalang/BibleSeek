import os
from dotenv import load_dotenv
import requests

# Load environment variables from the .env file
load_dotenv()

# Get the username and password from environment variables
username = os.getenv("GATEWAY_USERNAME")
password = os.getenv("GATEWAY_PASSWORD")
print("Username: ", username, "Password: ", password)

# Check if the username and password are correctly retrieved

if username is None or password is None:
    print("Error: Please check your .env file for missing variables.")
else:
    # URL for requesting an access token
    url = 'https://api.biblegateway.com/2/request_access_token'
    
    params = {
        'username': username,
        'password': password
    }

    # Send POST request to get the access token
    response = requests.post(url, data=params)

    # Parse the JSON response
    response_data = response.json()
    print(response_data)
    # Check for errors and extract the token
    if 'access_token' in response_data:
        access_token = response_data['access_token']
        print(f"Access Token: {access_token}")
    else:
        print("Wait")
        #print(f"Error: {response_data['error']['errmsg']}")
