from typing import List, Dict
import google.generativeai as genai
from dotenv import load_dotenv
import os

# --- Initialization ---
# Load environment variables from a .env file
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# It's good practice to ensure the key was actually loaded
# if not GOOGLE_API_KEY:
#     raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

# Configure the library with your API key
genai.configure(api_key=GOOGLE_API_KEY)


class Fuser:
    """
    A class to fuse multiple agent text responses into a single,
    coherent summary using a generative model.
    """
    def __init__(self):
        """Initializes the Fuser with a Gemini model instance."""
        self.model = genai.GenerativeModel("gemini-2.0-flash-lite")

    async def fuse(self, user_message: str, agent_responses: List[Dict]) -> str:
        """
        Combines multiple agent responses into one coherent answer using Gemini.

        Args:
            user_message: The original message/query from the user.
            agent_responses: A list of dictionaries, where each dict represents
                             an agent's response.

        Returns:
            A single, synthesized string response.
        """
        # Construct a detailed prompt for the model
        prompt_parts = [
            "You are a helpful assistant. Your job is to synthesize information from different expert agents into a single, unified, and natural-sounding response.",
            "Do not list the responses from each agent. Instead, combine their insights to directly answer the user's request in a comprehensive way.",
            f"\nUSER'S ORIGINAL REQUEST: '{user_message}'\n",
            "---",
            "INFORMATION FROM AGENTS:",
        ]
        print("agent response: ", agent_responses)
        # Append each agent's data to the prompt context
        for r in agent_responses:
            agent_name = r.get('agent', 'Unnamed Agent')
            # Handle both dictionary and simple string data
            agent_data = r.get('data', {})
            if isinstance(agent_data, dict):
                data_content = agent_data.get('message', str(agent_data))
            else:
                data_content = str(agent_data)
            
            prompt_parts.append(f"\n[{agent_name}]: {data_content}")
        
        final_prompt = "\n".join(prompt_parts)

        # Asynchronously generate the content
        response = await self.model.generate_content_async(final_prompt)
        
        return response.text