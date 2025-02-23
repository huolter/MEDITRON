# main.py
import os
import signal
import sys
import time
import asyncio
import requests

from dotenv import load_dotenv
from openai import OpenAI

from research import get_medical_advice  # Import the research function
from generate_final_audio import from_advice_doc_to_audio_script

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ConversationConfig
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

# Load environment variables
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_KEY")
PERPLEXITY_KEY = os.getenv("PERPLEXITY_KEY")
WAIT_TIME_SECONDS = 10
TRIAGO_AGENT_ID = "ElVoXXU3GzWLADpFa4vL"
MEDIKA0_ID = "m494ytPpnrp2NkYRa0sF"


def append_to_dossier(content, filename="dossier.txt"):
    """Append content to the dossier with a timestamp."""
    try:
        with open(filename, 'a', encoding='utf-8') as file:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            file.write(f"\n--- Updated: {timestamp} ---\n")
            file.write(content + "\n")
        print(f"Dossier updated at {timestamp}")
    except Exception as e:
        print(f"Error appending to dossier: {e}")

def initialize_dossier(filename="dossier.txt"):
    """Create (or overwrite) the dossier file with a header."""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write("=== MEDICAL CONSULTATION DOSSIER ===\n\n")
        print(f"Dossier initialized.")
    except Exception as e:
        print(f"Error initializing dossier: {e}")



def save_triago_to_dossier(conversation_data, research_context, filename="dossier.txt"):
    """Save Triago conversation and research data to the dossier."""

    content = "TRIAGE CONVERSATION SUMMARY:\n"
    content += "-" * 50 + "\n"
    content += conversation_data['summary'] + "\n\n"

    content += "TRIAGE COLLECTED DATA:\n"
    content += "-" * 50 + "\n"
    for key, value in conversation_data['collected_data'].items():
        content += f"{key}: {value}\n"
    content += "\n"

    content += "RESEARCH CONTEXT:\n"
    content += "-" * 50 + "\n"
    content += research_context + "\n\n"

    append_to_dossier(content, filename)


def save_medika_to_dossier(medika_conversation_data, filename="dossier.txt"):
    """Save Medika conversation data to the dossier."""

    content = "MEDIKA CONVERSATION SUMMARY:\n"
    content += "-" * 50 + "\n"
    content += medika_conversation_data['summary'] + "\n\n"

    content += "MEDIKA COLLECTED DATA:\n"
    content += "-" * 50 + "\n"
    for key, value in medika_conversation_data['collected_data'].items():
        content += f"{key}: {value}\n"
    content += "\n"

    append_to_dossier(content, filename)

def save_expert_recommendations(recommendations, filename="dossier.txt"):
    """Save expert recommendations to the dossier."""
    content = "EXPERT RECOMMENDATIONS:\n"
    content += "-" * 50 + "\n"
    content += recommendations + "\n\n"
    append_to_dossier(content, filename)


def read_dossier_simple(filename="dossier.txt"):
    """Read the dossier file."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading dossier: {e}")
        return None


def get_research_context(conversation_data):
    """Generate research context using Perplexity AI."""
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
                "You are an AI medical research assistant. Provide concise answers to user questions, supporting a "
                "Doctor in assessing a patient. Given a triage call summary, provide 1. possible causes and 2. "
                "follow up questions for the condition. Be concrete, direct, and summarize findings practically."
            ),
        },
        {
            "role": "user",
            "content": conversation_context,
        },
    ]

    client = OpenAI(api_key=PERPLEXITY_KEY, base_url="https://api.perplexity.ai")

    try:
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in research context generation: {e}")
        return None


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


def check_end_conversation(transcript, conversation):
    """Check if the conversation should end based on user transcript."""
    end_phrases = ["goodbye", "end call", "bye", "exit", "stop", "end conversation"]
    if any(phrase in transcript.lower() for phrase in end_phrases):
        print("Ending conversation based on voice command.")
        conversation.end_session()
        return True
    return False


def talk_to_dr_triago():
    """Initiate and manage conversation with Dr. Triago."""
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    conversation = Conversation(
        client,
        TRIAGO_AGENT_ID,
        requires_auth=bool(ELEVENLABS_API_KEY),
        audio_interface=DefaultAudioInterface(),
        callback_agent_response=lambda response: print(f"Agent: {response}"),
        callback_agent_response_correction=lambda original, corrected: print(f"Agent: {original} -> {corrected}"),
        callback_user_transcript=lambda transcript: (
            print(f"User: {transcript}"),
            check_end_conversation(transcript, conversation)
        ),
    )

    conversation.start_session()
    signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())
    conversation_id = conversation.wait_for_session_end()
    print(f"Conversation ID: {conversation_id}")
    return conversation_id


def talk_to_dr_medika():
    """Initiate and manage conversation with Dr. Medika."""
    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        dossier = read_dossier_simple()
        if not dossier:
            print("Error: Could not read dossier")
            return

        medika_system_prompt = (
            "You are Doctor Medika, a medical professional conducting a comprehensive follow-up with a patient. "
            "The patient has already described their initial complaints to Doctor Triago, and your role is to perform a deep evaluation based on that information. "
            "\n\n### Your Objectives: "
            "\n- Start by briefly mentioning what you already know, in a sentence, and ask for confirmation. "
            "\n- Conduct a thorough medical analysis by asking all necessary ADITIONAL questions. "
            "\n- Gather detailed information about symptoms, medical history, lifestyle factors, and any other relevant context. "
            "\n- Use the provided triage data and supplement it with additional research if needed. "
            "\n- Ask one question at a time to maintain clarity and focus. "
            "\n- If necessary, guide the patient through self-examinations or observations that could help refine the diagnosis. "
            "\n- Explore possible causes and treatment options, ensuring no important detail is overlooked. "
            "\n\n### Conversation Flow: "
            "\n1. Start by confirming key details from the triage report to ensure accuracy. "
            "\n2. Ask all necessary follow-up questions, focusing on depth and precision. Take your time to gather all critical information. "
            "\n3. If needed, research additional details and ask clarifying questions to refine your assessment. "
            "\n4. When you believe you have enough information, say: "
            '\n   "Okay, I think we have gathered enough details. Let me discuss this with my team." '
            "\n   However, remain available and continue the conversation until the patient signals they are ready to end it. "
            "\n5. Close the consultation by reassuring the patient and letting them know you will review the case with your medical team. "
            "\n\n### Patient Background: "
            f"\nContext and medical history for this patient:\n\n{dossier}"
            )
        print ("------------")
        print (medika_system_prompt)
        print ("------------")

        conversation_override = {
            "agent": {
                "prompt": {
                    "prompt": medika_system_prompt
                }
            }
        }

        config = ConversationConfig(
            conversation_config_override=conversation_override
        )

        print("Starting conversation with Dr. Medika...")

        def handle_agent_response(response):
            print(f"Dr. Medika: {response}")

        def handle_transcript(transcript):
            print(f"User: {transcript}")
            return check_end_conversation(transcript, conversation)

        conversation = Conversation(
            client,
            MEDIKA0_ID,
            requires_auth=True,
            audio_interface=DefaultAudioInterface(),
            callback_agent_response=handle_agent_response,
            callback_agent_response_correction=lambda original, corrected: print(
                f"Dr. Medika correction: {original} -> {corrected}"),
            callback_user_transcript=handle_transcript,
            config=config
        )

        conversation.start_session()
        signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())
        conversation_id = conversation.wait_for_session_end()
        print(f"Conversation ID: {conversation_id}")
        return conversation_id

    except Exception as e:
        print(f"An error occurred in talk_to_dr_medika: {str(e)}")
        return None


async def main():
    """Main function to orchestrate the conversations and data processing."""
    initialize_dossier() # Initialize the dossier at the start

    print("Talking to Dr Triago...")
    triago_conversation_id = talk_to_dr_triago()

    print(f"\nWaiting {WAIT_TIME_SECONDS} seconds for data processing...")
    for i in range(WAIT_TIME_SECONDS, 0, -1):
        sys.stdout.write(f"\rTime remaining: {i} seconds...")
        sys.stdout.flush()
        time.sleep(1)
    print("\n")

    print("Getting context and info from call...")
    triago_conversation_data = get_conversation_data(triago_conversation_id)

    if not triago_conversation_data:
        print("Failed to get conversation data. Creating minimal dossier...")
        triago_conversation_data = {
            'summary': f"Conversation ID: {triago_conversation_id}. Failed to retrieve detailed summary.",
            'collected_data': {'error': 'Data retrieval failed'}
        }
        level_1_context = "Unable to generate research context due to data retrieval failure."
    else:
        print("\nConversation Summary:")
        print(triago_conversation_data['summary'])

        print("\nCollected Data:")
        for key, value in triago_conversation_data['collected_data'].items():
            print(f"{key}: {value}")

        print("\nGenerating research context...")
        level_1_context = get_research_context(triago_conversation_data)

        if not level_1_context:
            level_1_context = "Failed to generate research context."
            print("Failed to generate research context")

    save_triago_to_dossier(triago_conversation_data, level_1_context)


    print("\nPreparing context for Dr Medika...")
    print("Instantiating Dr Medika...")
    print("Starting call with Dr Medika...")
    medika_conversation_id = talk_to_dr_medika()
    print(f"Finished consultation with Dr Medika. Conversation ID: {medika_conversation_id}")

    print(f"\nWaiting {WAIT_TIME_SECONDS} seconds for Medika data processing...")
    for i in range(WAIT_TIME_SECONDS, 0, -1):
        sys.stdout.write(f"\rTime remaining: {i} seconds...")
        sys.stdout.flush()
        time.sleep(1)
    print("\n")

    medika_conversation_data = get_conversation_data(medika_conversation_id)
    if not medika_conversation_data:
        print("Failed to get conversation data from Medika. Saving dossier without Medika data...")
        medika_conversation_data = {
            'summary': f"Conversation ID: {medika_conversation_id}. Failed to retrieve detailed summary.",
            'collected_data': {'error': 'Data retrieval failed'}
        }

    save_medika_to_dossier(medika_conversation_data)

    # --- New Expert Research Step ---
    print("\nPerforming expert research and assessment...")
    dossier_content = read_dossier_simple()
    if dossier_content:
        final_advice = await get_medical_advice("dossier.txt")
        if final_advice:
            save_expert_recommendations(final_advice)
            print("Expert recommendations saved to dossier.")
        else:
            print("Failed to get expert recommendations.")
    else:
        print("Failed to read dossier content for expert research.")

    print ("generating final audio mesage...")
    from_advice_doc_to_audio_script()
    print ("bye!")

if __name__ == "__main__":
    asyncio.run(main())