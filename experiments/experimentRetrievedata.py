import os
from dotenv import load_dotenv

import os
import signal
import sys

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

# Load environment variables from .env file
load_dotenv()

api_key=os.getenv("ELEVENLABS_KEY")
agent_id = "ElVoXXU3GzWLADpFa4vL"

client = ElevenLabs(api_key=api_key)

