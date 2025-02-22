import os
from dotenv import load_dotenv
import signal
import sys
import time
from threading import Timer

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
from elevenlabs import ConversationalConfig, PromptAgentToolsItem_System

from elevenlabs import (
    ConversationalConfig,
    ElevenLabs,
    AgentConfig,
    PromptAgent,
    PromptAgentToolsItem_System
)

def check_end_conversation(transcript, conversation):
    # List of phrases that will end the conversation
    end_phrases = ["goodbye", "end call", "bye", "exit", "stop", "end conversation"]
    if any(phrase in transcript.lower() for phrase in end_phrases):
        print("Ending conversation based on voice command.")
        conversation.end_session()
        return True
    return False

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("ELEVENLABS_KEY")
agent_id = "ElVoXXU3GzWLADpFa4vL"

client = ElevenLabs(api_key=api_key)




conversation = Conversation(
    client,
    agent_id,
    requires_auth=bool(api_key),
    audio_interface=DefaultAudioInterface(),
    callback_agent_response=lambda response: print(f"Agent: {response}"),
    callback_agent_response_correction=lambda original, corrected: print(f"Agent: {original} -> {corrected}"),
    callback_user_transcript=lambda transcript: (
        print(f"User: {transcript}"),
        check_end_conversation(transcript, conversation)
    ),
)

# Start the conversation session
conversation.start_session()

# Function to end the session after a timeout
def end_conversation():
    print("Ending conversation automatically due to timeout.")
    conversation.end_session()



# Handle signal interrupts to end the session gracefully
signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())

# Wait for the session to end and get the conversation ID
conversation_id = conversation.wait_for_session_end()
print(f"Conversation ID: {conversation_id}")
