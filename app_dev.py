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
from elevenlabs import ConversationalConfig, PromptAgentToolsItem_System

# Load environment variables from .env file
load_dotenv()

elevenlabs_api_key = os.getenv("ELEVENLABS_KEY")
perplexity_key = os.getenv("PERPLEXITY_KEY")
fal_api_key = os.getenv("FAL_KEY")

triago_agent_id = "ElVoXXU3GzWLADpFa4vL"

WAIT_TIME_SECONDS = 10 # waiting time for data processing post convo
INACTIVITY_TIMEOUT = 30  # Timeout after 30 seconds of inactivity

def get_research_context(conversation_data):
    """Generate research context using the Perplexity AI"""
    # Format conversation data
    conversation_context = f"""Conversation Summary:
{conversation_data['summary']}

Collected Data:
"""
    for key, value in conversation_data['collected_data'].items():
        conversation_context += f"{key}: {value}\n"

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
            "content": conversation_context,
        },
    ]

    client = OpenAI(api_key=perplexity_key, base_url="https://api.perplexity.ai")

    try:
        response = client.chat.completions.create(
            model="sonar",
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in research context generation: {e}")
        return None

def get_conversation_data(conversation_id):
    """Retrieve and parse conversation data from ElevenLabs API"""
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {"xi-api-key": elevenlabs_api_key}
    
    try:
        response = requests.get(url, headers=headers).json()
        
        # Extract summary and collected data
        summary = response['analysis']['transcript_summary']
        data_collection_results = response["analysis"]["data_collection_results"]
        
        # Create a dictionary to store collected data
        collected_data = {}
        for key, item in data_collection_results.items():
            collected_data[item['data_collection_id']] = item['value']
        
        return {
            'summary': summary,
            'collected_data': collected_data
        }
    except Exception as e:
        print(f"Error retrieving conversation data: {e}")
        return None


def end_conversation_automatically(conversation):
    print("Ending conversation automatically due to timeout.")
    conversation.end_session()

def check_end_conversation(transcript, conversation):
    # List of phrases that will end the conversation
    end_phrases = ["goodbye", "end call", "bye", "exit", "stop", "end conversation"]
    if any(phrase in transcript.lower() for phrase in end_phrases):
        print("Ending conversation based on voice command.")
        conversation.end_session()
        return True
    
    # Reset the inactivity timer upon user input to prevent premature timeout
    inactivity_timer = Timer(INACTIVITY_TIMEOUT, lambda: end_conversation_automatically(conversation))
    inactivity_timer.start()
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

    # Handle signal interrupts to end the session gracefully
    signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())

    # Initiate inactivity timer
    inactivity_timer = Timer(INACTIVITY_TIMEOUT, lambda: end_conversation_automatically(conversation))
    inactivity_timer.start()

    # Wait for the session to end and get the conversation ID
    conversation_id = conversation.wait_for_session_end()
    inactivity_timer.cancel()  # Cancel inactivity timer on session end
    print(f"Conversation ID: {conversation_id}")
    return conversation_id


def save_to_dossier(conversation_data, research_context, filename="dossier.txt"):
    """Save conversation data, collected data, and research context to a file"""
    try:
        # Remove existing dossier if it exists
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Removed existing {filename}")

        # Create new dossier
        with open(filename, 'w', encoding='utf-8') as file:
            # Write conversation summary
            file.write("=== MEDICAL CONSULTATION DOSSIER ===\n\n")
            file.write("CONVERSATION SUMMARY:\n")
            file.write("-" * 50 + "\n")
            file.write(conversation_data['summary'])
            file.write("\n\n")

            # Write collected data
            file.write("COLLECTED DATA:\n")
            file.write("-" * 50 + "\n")
            for key, value in conversation_data['collected_data'].items():
                file.write(f"{key}: {value}\n")
            file.write("\n")

            # Write research context
            file.write("RESEARCH CONTEXT:\n")
            file.write("-" * 50 + "\n")
            file.write(research_context)
            file.write("\n\n")

            # Write timestamp
            file.write("-" * 50 + "\n")
            file.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        print(f"\nNew dossier created successfully: {filename}")
        return True
    except Exception as e:
        print(f"Error saving dossier: {e}")
        return False


def main():
    print("Talking to Dr Triago...")
    triago_conversation_id = talk_to_dr_triago()
    
    print(f"\nWaiting {WAIT_TIME_SECONDS} seconds for data processing...")
    for i in range(WAIT_TIME_SECONDS, 0, -1):
        sys.stdout.write(f"\rTime remaining: {i} seconds...")
        sys.stdout.flush()
        time.sleep(1)
    print("\n")
    
    print("Getting context and info from call...")
    conversation_data = get_conversation_data(triago_conversation_id)
    
    if conversation_data:
        print("\nConversation Summary:")
        print(conversation_data['summary'])
        
        print("\nCollected Data:")
        for key, value in conversation_data['collected_data'].items():
            print(f"{key}: {value}")
        
        print("\nGenerating research context...")
        level_1_context = get_research_context(conversation_data)
        
        if level_1_context:
            print("\nResearch Context:")
            print(level_1_context)
            
            # Save all information to dossier
            save_to_dossier(conversation_data, level_1_context)
        else:
            print("Failed to generate research context")
    
    print("\nPreparing context for Dr Medika...")
    print("Instantiating Dr Medika...")
    print("Starting call with Dr Medika...")

if __name__ == "__main__":
    main()