from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

YOUR_API_KEY = os.getenv("PERPLEXITY_KEY")



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
            '''Coordination issues, unsteadiness, brain fog, weakness in legs and arms (especially legs when walking), intermittent joint pains, pain in left heel, pain under left and right ribs, blurry vision (comes and goes independently), elevated resting heart rate (even while sleeping), fatigue (flu-like), pressure on sides of head when walking, flushing of cheeks, and itching on back.'''
        ),
    },
]

client = OpenAI(api_key=YOUR_API_KEY, base_url="https://api.perplexity.ai")

# chat completion without streaming
response = client.chat.completions.create(
    model="sonar",
    messages=messages,
)

content = response.choices[0].message.content


print(content)

