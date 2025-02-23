import os
from dotenv import load_dotenv

import os
import signal
import sys

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

import os
import signal
import sys
import time
import requests
from dotenv import load_dotenv
from openai import OpenAI

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ConversationConfig
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
from elevenlabs import ConversationalConfig, PromptAgentToolsItem_System, AgentConfig, PromptAgent

# Load environment variables
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_KEY")
PERPLEXITY_KEY = os.getenv("PERPLEXITY_KEY")
WAIT_TIME_SECONDS = 10
TRIAGO_AGENT_ID = "ElVoXXU3GzWLADpFa4vL"
MEDIKA0_ID = "m494ytPpnrp2NkYRa0sF"

# Load environment variables from .env file
load_dotenv()

api_key=os.getenv("ELEVENLABS_KEY")


def get_conversation_data(conversation_id):
    """Retrieve and parse conversation data from ElevenLabs API."""
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()

        if 'analysis' not in data or 'transcript_summary' not in data['analysis'] or 'data_collection_results' not in \
                data['analysis']:
            print("Error: Missing data in response")
            return None

        summary = data['analysis']['transcript_summary']
        data_collection_results = data['analysis']['data_collection_results']

        collected_data = {}
        for key, item in data_collection_results.items():
            collected_data[item['data_collection_id']] = item['value']

        return {
            'summary': summary,
            'collected_data': collected_data
        }
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None
    except KeyError as e:
        print(f"Error accessing data in response: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error retrieving conversation data: {e}")
        return None



conversation_data = get_conversation_data(conversation_key)

print (conversation_data)