from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

YOUR_API_KEY = os.getenv("PERPLEXITY_KEY")

conversation_context = '''Conversation Summary:
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



messages = [
    {
        "role": "system",
        "content": (
            "You are an AI medical research assistant and you need to "
            "provide with consice answers to the user questions."
            "You are supporting a Doctor in assesing a patient."
            "You will be provided with the summary of the triage call"
            "Provide with 1. possible causes and 2. follow up questions for the given condition specified."
            "Be concrete, direct, and summarize findings in a practical way. Do not add any other content or comments."
        ),
    },
    {   
        "role": "user",
        "content": (
            conversation_context
        ),
    },
]

client = OpenAI(api_key=YOUR_API_KEY, base_url="https://api.perplexity.ai")

# chat completion without streaming
response = client.chat.completions.create(
    model="sonar",
    messages=messages,
)

level_1_context = response.choices[0].message.content


print(level_1_context)

