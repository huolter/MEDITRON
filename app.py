# main.py
"""Medical consultation system integrating triage, follow-up, and expert analysis."""

import asyncio
import os
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Optional

import requests
from dotenv import load_dotenv
from openai import OpenAI

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ConversationConfig
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

from generate_final_audio import from_advice_doc_to_audio_script
from research import get_medical_advice

# Constants
DOSSIER_FILE = "dossier.txt"
WAIT_TIME_SECONDS = 10
TRIAGO_AGENT_ID = "ElVoXXU3GzWLADpFa4vL"
MEDIKA0_ID = "m494ytPpnrp2NkYRa0sF"
SECTION_SEPARATOR = "-" * 50

# Load environment variables
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_KEY")
PERPLEXITY_KEY = os.getenv("PERPLEXITY_KEY")


class DossierManager:
    """Manages the medical consultation dossier file."""

    @staticmethod
    def _append(content: str, filename: str = DOSSIER_FILE) -> None:
        """Append content to the dossier with a timestamp."""
        try:
            with open(filename, "a", encoding="utf-8") as file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                file.write(f"\n--- Updated: {timestamp} ---\n{content}\n")
            print(f"Dossier updated at {timestamp}")
        except IOError as e:
            print(f"Error appending to dossier: {e}")

    @staticmethod
    def initialize(filename: str = DOSSIER_FILE) -> None:
        """Initialize or reset the dossier file with a header."""
        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write("=== MEDICAL CONSULTATION DOSSIER ===\n\n")
            print("Dossier initialized.")
        except IOError as e:
            print(f"Error initializing dossier: {e}")

    @staticmethod
    def read(filename: str = DOSSIER_FILE) -> Optional[str]:
        """Read the entire dossier content."""
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return file.read()
        except IOError as e:
            print(f"Error reading dossier: {e}")
            return None

    @staticmethod
    def save_triago_data(conversation_data: Dict, research_context: str, filename: str = DOSSIER_FILE) -> None:
        """Save Triago conversation and research data to the dossier."""
        content = (
            f"TRIAGE CONVERSATION SUMMARY:\n{SECTION_SEPARATOR}\n{conversation_data['summary']}\n\n"
            f"TRIAGE COLLECTED DATA:\n{SECTION_SEPARATOR}\n"
            f"{_format_dict(conversation_data['collected_data'])}\n\n"
            f"RESEARCH CONTEXT:\n{SECTION_SEPARATOR}\n{research_context}\n"
        )
        DossierManager._append(content, filename)

    @staticmethod
    def save_medika_data(conversation_data: Dict, filename: str = DOSSIER_FILE) -> None:
        """Save Medika conversation data to the dossier."""
        content = (
            f"MEDIKA CONVERSATION SUMMARY:\n{SECTION_SEPARATOR}\n{conversation_data['summary']}\n\n"
            f"MEDIKA COLLECTED DATA:\n{SECTION_SEPARATOR}\n"
            f"{_format_dict(conversation_data['collected_data'])}\n"
        )
        DossierManager._append(content, filename)

    @staticmethod
    def save_expert_recommendations(recommendations: str, filename: str = DOSSIER_FILE) -> None:
        """Save expert recommendations to the dossier."""
        content = f"EXPERT RECOMMENDATIONS:\n{SECTION_SEPARATOR}\n{recommendations}\n"
        DossierManager._append(content, filename)


def _format_dict(data: Dict) -> str:
    """Format dictionary data into a string."""
    return "\n".join(f"{key}: {value}" for key, value in data.items())


class ConversationHandler:
    """Handles interactions with ElevenLabs conversational agents."""

    def __init__(self, api_key: str):
        self.client = ElevenLabs(api_key=api_key)

    def _check_end_conversation(self, transcript: str, conversation: Conversation) -> bool:
        """Check if the conversation should end based on user input."""
        end_phrases = {"goodbye", "end call", "bye", "exit", "stop", "end conversation"}
        if any(phrase in transcript.lower() for phrase in end_phrases):
            print("Ending conversation based on voice command.")
            conversation.end_session()
            return True
        return False

    def talk_to_triago(self) -> Optional[str]:
        """Initiate and manage conversation with Dr. Triago."""
        conversation = Conversation(
            self.client,
            TRIAGO_AGENT_ID,
            requires_auth=bool(ELEVENLABS_API_KEY),
            audio_interface=DefaultAudioInterface(),
            callback_agent_response=lambda response: print(f"Agent: {response}"),
            callback_agent_response_correction=lambda orig, corr: print(f"Agent: {orig} -> {corr}"),
            callback_user_transcript=lambda transcript: (
                print(f"User: {transcript}"),
                self._check_end_conversation(transcript, conversation),
            ),
        )
        return self._run_conversation(conversation)

    def talk_to_medika(self, dossier_content: str) -> Optional[str]:
        """Initiate and manage conversation with Dr. Medika."""
        medika_prompt = (
            "You are Doctor Medika, a medical professional conducting a comprehensive follow-up with a patient. "
            "The patient has already described their initial complaints to Doctor Triago, and your role is to perform a deep evaluation based on that information. "
            "\n\n### Your Objectives: "
            "\n- Start by briefly mentioning what you already know, in a sentence, and ask for confirmation. "
            "\n- Conduct a thorough medical analysis by asking all necessary ADDITIONAL questions. "
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
            f"\n\n### Patient Background: \nContext and medical history for this patient:\n\n{dossier_content}"
        )

        config = ConversationConfig(
            conversation_config_override={"agent": {"prompt": {"prompt": medika_prompt}}}
        )

        conversation = Conversation(
            self.client,
            MEDIKA0_ID,
            requires_auth=True,
            audio_interface=DefaultAudioInterface(),
            callback_agent_response=lambda response: print(f"Dr. Medika: {response}"),
            callback_agent_response_correction=lambda orig, corr: print(f"Dr. Medika correction: {orig} -> {corr}"),
            callback_user_transcript=lambda transcript: (
                print(f"User: {transcript}"),
                self._check_end_conversation(transcript, conversation),
            ),
            config=config,
        )
        print("Starting conversation with Dr. Medika...")
        return self._run_conversation(conversation)

    def _run_conversation(self, conversation: Conversation) -> Optional[str]:
        """Run a conversation session and return the conversation ID."""
        try:
            conversation.start_session()
            signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())
            conversation_id = conversation.wait_for_session_end()
            print(f"Conversation ID: {conversation_id}")
            return conversation_id
        except Exception as e:
            print(f"Error during conversation: {e}")
            return None


class ResearchAssistant:
    """Handles research and data retrieval tasks."""

    @staticmethod
    def get_conversation_data(conversation_id: str) -> Optional[Dict]:
        """Retrieve conversation data from ElevenLabs API."""
        url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
        headers = {"xi-api-key": ELEVENLABS_API_KEY}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if not all(k in data.get("analysis", {}) for k in ["transcript_summary", "data_collection_results"]):
                print("Error: Missing data in response")
                return None

            collected_data = {
                item["data_collection_id"]: item["value"]
                for key, item in data["analysis"]["data_collection_results"].items()
            }
            return {
                "summary": data["analysis"]["transcript_summary"],
                "collected_data": collected_data,
            }
        except requests.RequestException as e:
            print(f"Error making API request: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"Error parsing response data: {e}")
            return None

    @staticmethod
    def get_research_context(conversation_data: Dict) -> Optional[str]:
        """Generate research context using Perplexity AI."""
        context = (
            f"Conversation Summary:\n{conversation_data['summary']}\n\n"
            f"Collected Data:\n{_format_dict(conversation_data['collected_data'])}"
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI medical research assistant. Provide concise answers to user questions, "
                    "supporting a Doctor in assessing a patient. Given a triage call summary, provide 1. possible "
                    "causes and 2. follow up questions for the condition. Be concrete, direct, and summarize "
                    "findings practically."
                ),
            },
            {"role": "user", "content": context},
        ]

        client = OpenAI(api_key=PERPLEXITY_KEY, base_url="https://api.perplexity.ai")
        try:
            response = client.chat.completions.create(model="sonar-pro", messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating research context: {e}")
            return None


async def main():
    """Orchestrate the medical consultation process."""
    dossier = DossierManager()
    conversation_handler = ConversationHandler(ELEVENLABS_API_KEY)
    research = ResearchAssistant()

    # Initialize dossier
    dossier.initialize()

    # Triago consultation
    print("Talking to Dr Triago...")
    triago_id = conversation_handler.talk_to_triago()
    await _wait_with_countdown(WAIT_TIME_SECONDS)

    # Process Triago data
    triago_data = research.get_conversation_data(triago_id) or {
        "summary": f"Conversation ID: {triago_id}. Failed to retrieve detailed summary.",
        "collected_data": {"error": "Data retrieval failed"},
    }
    print_conversation_data(triago_data)
    research_context = research.get_research_context(triago_data) or "Failed to generate research context."
    dossier.save_triago_data(triago_data, research_context)

    # Medika consultation
    print("\nPreparing context for Dr Medika...")
    dossier_content = dossier.read()
    if not dossier_content:
        print("Error: Could not read dossier for Medika consultation.")
        return

    medika_id = conversation_handler.talk_to_medika(dossier_content)
    await _wait_with_countdown(WAIT_TIME_SECONDS)

    # Process Medika data
    medika_data = research.get_conversation_data(medika_id) or {
        "summary": f"Conversation ID: {medika_id}. Failed to retrieve detailed summary.",
        "collected_data": {"error": "Data retrieval failed"},
    }
    dossier.save_medika_data(medika_data)

    # Expert recommendations
    print("\nPerforming expert research and assessment...")
    if dossier_content := dossier.read():
        if final_advice := await get_medical_advice(DOSSIER_FILE):
            dossier.save_expert_recommendations(final_advice)
            print("Expert recommendations saved to dossier.")
        else:
            print("Failed to get expert recommendations.")
    else:
        print("Failed to read dossier for expert research.")

    # Generate final audio
    print("Generating final audio message...")
    from_advice_doc_to_audio_script()
    print("Bye!")


async def _wait_with_countdown(seconds: int) -> None:
    """Display a countdown timer."""
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\rTime remaining: {i} seconds...")
        sys.stdout.flush()
        await asyncio.sleep(1)
    print("\n")


def print_conversation_data(data: Dict) -> None:
    """Print conversation summary and collected data."""
    print("\nConversation Summary:")
    print(data["summary"])
    print("\nCollected Data:")
    for key, value in data["collected_data"].items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())