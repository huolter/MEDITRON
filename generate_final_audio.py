import os
import uuid

from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import fal_client


voice_id = "XrExE9yKIg1WjnnlVkGX"

# Load environment variables
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_KEY")

client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
)


def from_advice_doc_to_audio_script():
    
    fal_api_key = os.getenv("FAL_KEY") # Get the API key here
    
    try:
        with open("final_advice.txt", "r") as file:
            medical_advice = file.read()
    except FileNotFoundError:
        return f"Error: File not found at path: {"final_advice.txt"}"
    except Exception as e:
        return f"Error reading file: {e}"

    full_prompt = (
        "The following is the medical report and final advice suggested for a patient. "
        "Based on this information, compose a short message that will then be read by the doctor "
        "(Start with \"Hello name, I am Doctor Medika...\") and then communicate the findings and "
        "suggestions to the patient. The patient will recieve this message as an audio message. "
        "Do not add any other comments or observations, just reply with the message as if it will be "
        "spoke by dr Medika. Be detailed and precise, give context and justification.\n\n"
        "Context:\n" + medical_advice
    )

    result = fal_client.subscribe(
    "fal-ai/any-llm",
    arguments={
        "model": "openai/gpt-4o",
        "prompt": full_prompt
    })
    
    response_text = result.get('output', 'No output received')
    text_to_speech_file(response_text)


def text_to_speech_file(text: str) -> str:
    """
    Converts text to speech and saves the output as an MP3 file.

    This function uses a specific client for text-to-speech conversion. It configures
    various parameters for the voice output and saves the resulting audio stream to an
    MP3 file with a unique name.

    Args:
        text (str): The text content to convert to speech.

    Returns:
        str: The file path where the audio file has been saved.
    """
    # Calling the text_to_speech conversion API with detailed parameters
    response = client.text_to_speech.convert(
        voice_id=voice_id,  
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2",  # use the turbo model for low latency, for other languages use the `eleven_multilingual_v2`
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    # Generating a unique file name for the output MP3 file
    save_file_path = f"{uuid.uuid4()}.mp3"
    # Writing the audio stream to the file

    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"A new audio file was saved successfully at {save_file_path}")

    # Return the path of the saved audio file
    return save_file_path


if __name__ == "__main__":
    from_advice_doc_to_audio_script()
    
    #text_to_speech_file("Hello, world! This is a test of the ElevenLabs API.")