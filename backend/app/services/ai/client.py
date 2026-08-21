import os
from dotenv import load_dotenv
from google import genai
from groq import Groq


load_dotenv()

# Choose model provider: "gemini" or "groq"
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")

if AI_PROVIDER == "gemini":
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
elif AI_PROVIDER == "groq":
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
else:
    raise ValueError("Invalid AI_PROVIDER")
