# research.py
import os
import asyncio
from dotenv import load_dotenv
import fal_client

# Load environment variables from .env file
load_dotenv()

async def fetch_response(model, context, prompt):
    """Fetch response asynchronously using fal_client.subscribe."""
    full_prompt = f"{context}\n\n{prompt}"
    api_key = os.getenv("FAL_KEY") # Get the API key here

    result = await asyncio.to_thread(
        fal_client.subscribe,
        "fal-ai/any-llm",
        arguments={
            "model": model,
            "prompt": full_prompt,
            "system_prompt": "",
            "api_key": api_key  # Include the API key directly in arguments
        }
    )

    response_text = result.get('output', 'No output received')
    return {
        "model": model,
        "prompt": prompt,
        "output": response_text
    }

async def research(context):
    """Conducts research with different AI models and perspectives (9 total iterations)."""
    diversity_prompts = [
        "Analyze this medical dossier with the precision of a specialist in the relevant field, focusing on diagnosis, treatment options, and medical best practices.",
        "Review this medical dossier from a holistic and integrative perspective, considering lifestyle, nutrition, mental health, and alternative approaches alongside conventional medicine.",
        "Evaluate this medical dossier through the lens of risk assessment, identifying potential complications, predicting disease progression, and highlighting preventive measures."
    ]

    models = [
        "google/gemini-pro-1.5",
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o-mini"
    ]

    tasks = []
    for model in models:
        for prompt in diversity_prompts:
            print(f"Using model {model} to assess: {prompt}")
            tasks.append(fetch_response(model, context, prompt))

    results = await asyncio.gather(*tasks)  # Run all tasks concurrently

    # Save research results (Optional:  You might not *always* want to save)
    with open("team_research.txt", "w", encoding="utf-8") as file:
        for result in results:
            file.write(f"### Model: {result['model']} ###\n")
            file.write(f"### Perspective: {result['prompt']} ###\n")
            file.write(result["output"] + "\n\n")

    return results

async def final_assessment(context, research_results):
    """Requests a final assessment considering all previous research."""
    combined_research = "\n\n".join(
        f"Model: {res['model']}\nPerspective: {res['prompt']}\n{res['output']}"
        for res in research_results
    )

    final_prompt = (
        "Review carefully the opinion of all voices in this research, "
        "consider the best course of action, and come up with a comprehensive final assessment. "
        "This final assessment will be used by the person's doctor to have a discussion on treatment and recommendations.\n\n"
        f"Context:\n{context}\n\nResearch Findings:\n{combined_research}"
    )

    final_response = await fetch_response("openai/gpt-4o", context, final_prompt)

    # Save final advice (Optional: You might not *always* want to save)
    with open("final_advice.txt", "w", encoding="utf-8") as file:
        file.write("This is the final advice based on the case review and discussed with the medical panel.\n\n")
        file.write(final_response["output"])
    return final_response["output"] # Return the output directly


async def get_medical_advice(dossier_filepath):
    """
    Reads a medical dossier, performs AI-powered research, and returns the final assessment.

    Args:
        dossier_filepath: The path to the file containing the medical dossier.

    Returns:
        A string containing the final medical advice.  Returns None on error.
    """
    try:
        with open(dossier_filepath, 'r', encoding='utf-8') as file:
            context = file.read()
    except FileNotFoundError:
        print(f"Error: Dossier file not found at {dossier_filepath}")
        return None
    except Exception as e:
        print(f"Error reading dossier file: {e}")
        return None

    try:
        research_results = await research(context)
        final_advice = await final_assessment(context, research_results)
        return final_advice
    except Exception as e:
        print(f"An error occurred during research or assessment: {e}")
        return None



if __name__ == "__main__":
    # Example usage when running research.py directly:
    async def run_main():
        advice = await get_medical_advice("dossier.txt")
        if advice:
            print("\nFinal Medical Advice:\n", advice)
    asyncio.run(run_main())





