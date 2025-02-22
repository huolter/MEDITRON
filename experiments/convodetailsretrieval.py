import os
from dotenv import load_dotenv
import signal
import sys
import time
from threading import Timer
import requests

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
elevenlabs_api_key = os.getenv("ELEVENLABS_KEY")
triago_agent_id = "ElVoXXU3GzWLADpFa4vL"
conversation_id = "xxhiVQVhkEvsv1kTdykO"

# Construct the URL with the conversation_id at the end
url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"

# Set headers with the API key from environment variables
headers = {"xi-api-key": elevenlabs_api_key}

# Make the request
response = requests.get(url, headers=headers).json()

summary = response['analysis']['transcript_summary']
data_collection_results = response["analysis"]["data_collection_results"]

print (summary)

for key, item in data_collection_results.items():
    data_id = item['data_collection_id']
    value = item['value']
    print(f"{data_id}: {value}")