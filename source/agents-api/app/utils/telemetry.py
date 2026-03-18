import os
from langsmith import Client, wrappers
from dotenv import load_dotenv
import openai

load_dotenv()

# LangSmith initialization
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "IT-Incident-Assistant"

client = Client()

# Globally wrap the OpenAI clients for automatic multi-agent tracing
traced_client = wrappers.wrap_openai(openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")))
traced_async_client = wrappers.wrap_openai(openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))

def track_cost(model: str, input_tokens: int, output_tokens: int):
    """Basic cost tracking logic."""
    rates = {
        "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
        "text-embedding-3-small": {"input": 0.02 / 1_000_000, "output": 0}
    }
    
    rate = rates.get(model, {"input": 0, "output": 0})
    cost = (input_tokens * rate["input"]) + (output_tokens * rate["output"])
    return cost
