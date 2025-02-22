import os
from dotenv import load_dotenv
import signal
import time
from elevenlabs import (
    ConversationalConfig,
    ElevenLabs,
    AgentConfig,
    PromptAgent,
)
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

# Load environment variables
load_dotenv()
elevenlabs_api_key = os.getenv("ELEVENLABS_KEY")

def read_dossier_simple(filename="dossier.txt"):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading dossier: {e}")
        return None

def check_end_conversation(transcript, conversation):
    end_phrases = ["goodbye", "end call", "bye", "exit", "stop", "end conversation"]
    if any(phrase in transcript.lower() for phrase in end_phrases):
        print("Ending conversation based on voice command.")
        conversation.end_session()
        return True
    return False

def main():
    try:
        # Initialize client
        client = ElevenLabs(api_key=elevenlabs_api_key)

        # Read dossier
        dossier = read_dossier_simple()
        if not dossier:
            print("Error: Could not read dossier")
            return

        # Create system prompt
        system_prompt = '''You are Medika, a doctor following up with a patient.
        Your job is to do a deep evaluation and ask all the needed questions.
        The info you collect will be used to define treatement.
        Ask no more than 10 questions.
        When finished, say 'ok, I think we have enough information, let me discuss with my team'
        and end conversation. 
        This is the context and background info for the patient you are talking to: ''' + dossier

        # Create agent
        print("Creating agent...")
        try:
            agent_response = client.conversational_ai.create_agent(
                name="Medika", 
                conversation_config=ConversationalConfig(
                    tts= {
        "voice_id": "56AoDkrOh6qfVPDXZ7Pt" # Optional: override the voice.
    },
                    agent=AgentConfig(
                        prompt=PromptAgent(
                            temperature="0.5",
                            prompt=system_prompt
                        ),
                        first_message="Hello, I am Doctor Medika, and I would like to discuss your complaints with you, is that ok?"
                    )
                )
            )
            # Extract the agent_id string
            agent_id = agent_response.agent_id
        except Exception as e:
            print(f"Error during agent creation: {e}")
            return

        if not agent_id:
            print("Error: Failed to create agent")
            return

        print(f"Agent ID: {agent_id}")

        # Wait for sufficient initialization time
        print("Waiting for agent to initialize...")
        time.sleep(10)

        # Create conversation
        print("Starting conversation...")
        try:
            conversation = Conversation(
                client=client,
                agent_id=agent_id,  # Ensure 'agent_id' is a simple string
                requires_auth=True,
                audio_interface=DefaultAudioInterface(),
                callback_agent_response=lambda response: print(f"Agent: {response}"),
                callback_agent_response_correction=lambda original, corrected: print(f"Agent: {original} -> {corrected}"),
                callback_user_transcript=lambda transcript: (
                    print(f"User: {transcript}"),
                    check_end_conversation(transcript, conversation)
                ),
            )
        except Exception as e:
            print(f"Error creating conversation: {e}")
            return

        # Handle signal interrupts
        signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())

        # Start conversation
        try:
            conversation.start_session()
            conversation_id = conversation.wait_for_session_end()
            print(f"Conversation ID: {conversation_id}")
        except Exception as e:
            print(f"Error during conversation session management: {e}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
