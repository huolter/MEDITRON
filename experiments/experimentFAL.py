import os
from dotenv import load_dotenv
import fal_client

example_prompt = '''Conversation Summary:
The conversation involves a health triage interaction between an AI assistant, 
Doctor Triago, and a user named Roberto. The AI collects basic information from Roberto, 
who is 90 years old and complains of a very high fever with no other symptoms. 
Doctor Triago informs Roberto that Doctor Medika will follow up soon. 
The conversation ends with Roberto thanking the AI and saying goodbye. 
The AI assistant then initiates an end call procedure, 
responding with a polite farewell message. 
The interaction is brief, professional, and focused on gathering essential 
health information for further medical follow-up.

Collected Data:
age: 90
health complaints: very high fever
name: Roberto'''

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("FAL_KEY")

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])

result = fal_client.subscribe(
    "fal-ai/any-llm",
    arguments={
        "model": "openai/gpt-4o-mini",
        "reasoning": False,
        "prompt": "The following are the Doctor Notes, analyze them and suggest course of action: " + example_prompt
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)

# Separate and print the result and reasoning
print("\nResult:")
print("-" * 50)
print(result['output'])


