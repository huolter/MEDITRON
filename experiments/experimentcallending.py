import os
from dotenv import load_dotenv
import signal
import sys
import time
from threading import Timer
import requests
from openai import OpenAI
import fal_client

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
from elevenlabs import ConversationalConfig, PromptAgentToolsItem_System, AgentConfig, PromptAgent

elevenlabs_api_key = os.getenv("ELEVENLABS_KEY")

agent_id = "lVqndem67gv0xgROgIJy"
client = ElevenLabs(api_key=elevenlabs_api_key)

def handle_user_transcript(transcript):
    print(f"User: {transcript}")
    if "goodbye" in transcript.lower():
        print("Goodbye mentioned. Ending conversation...")
        conversation.end_session()

conversation = Conversation(
    client,
    agent_id,
    requires_auth=bool(elevenlabs_api_key),
    audio_interface=DefaultAudioInterface(),
    callback_agent_response=lambda response: print(f"Agent: {response}"),
    callback_agent_response_correction=lambda original, corrected: print(f"Agent: {original} -> {corrected}"),
    callback_user_transcript=handle_user_transcript
)

# Add signal handler for clean shutdown
signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())

conversation.start_session()

# Wait for the conversation to end and get the conversation ID
conversation_id = conversation.wait_for_session_end()
print(f"Conversation ID: {conversation_id}")
