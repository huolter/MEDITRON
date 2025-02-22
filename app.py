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

# Load environment variables from .env file
load_dotenv()

elevenlabs_api_key = os.getenv("ELEVENLABS_KEY")
triago_agent_id = "ElVoXXU3GzWLADpFa4vL"


def check_end_conversation(transcript, conversation):
    # List of phrases that will end the conversation
    end_phrases = ["goodbye", "end call", "bye", "exit", "stop", "end conversation"]
    if any(phrase in transcript.lower() for phrase in end_phrases):
        print("Ending conversation based on voice command.")
        conversation.end_session()
        return True
    return False


def talk_to_dr_triago():
    client = ElevenLabs(api_key=elevenlabs_api_key)
    conversation = Conversation(
    client,
    triago_agent_id,
    requires_auth=bool(elevenlabs_api_key),
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
    return conversation_id



def main():
    print ("talking to Dr Triago...")
    triago_conversation_id = talk_to_dr_triago()
    print ("getting context and info from call...")
    print ("instruct research agent...")
    print ("prepare context for Dr Medika...")
    print ("instantiate Dr Medika...")
    print ("call with Dr Medika...")


main()

