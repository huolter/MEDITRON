import os
from dotenv import load_dotenv
import fal_client

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("FAL_KEY")

with open('deep_medical_analysis_prompt.txt', 'r') as file:
    base_prompt = file.read()

with open('dossier.txt', 'r') as file:
    context = file.read()

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])


prompt = base_prompt + "\n\n\n" + context

print (prompt)

result = fal_client.subscribe(
    "fal-ai/any-llm",
    arguments={
        "model": "openai/gpt-4o",
        "prompt": prompt,
        "system_prompt": ""
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result["output"])






