import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("FAL_KEY")

import fal_client

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])

result = fal_client.subscribe(
    "fal-ai/any-llm",
    arguments={
        "prompt": "What is the meaning of life?"
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result)

import fal_client

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])

result = fal_client.subscribe(
    "fal-ai/wizper",
    arguments={
        "audio_url": "https://ihlhivqvotguuqycfcvj.supabase.co/storage/v1/object/public/public-text-to-speech/scratch-testing/earth-history-19mins.mp3"
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result)

