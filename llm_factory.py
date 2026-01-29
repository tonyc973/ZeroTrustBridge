import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMFactory:
    """
    Returns a standard OpenAI Client configured for either:
    1. Local Llama Server (http://localhost:8080/v1)
    2. Real OpenAI API (https://api.openai.com/v1)
    """
    @staticmethod
    def create_client(provider: str):
        if provider == "local":
            print("🔌 Connecting to LOCAL Llama Server...")
            return OpenAI(
                base_url="http://localhost:8080/v1",
                api_key="sk-no-key-required" # Local server ignores this
            )
        
        elif provider == "openai":
            print("🔌 Connecting to CLOUD OpenAI API...")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("❌ OPENAI_API_KEY is missing in .env")
            return OpenAI(api_key=api_key)
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
