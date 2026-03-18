import asyncio
from agents import Agent, Runner
from dotenv import load_dotenv

load_dotenv("../.env")
load_dotenv()

async def debug():
    agent = Agent(name="Test Agent", instructions="You are a test agent.")
    result = await Runner.run(agent, "Hi")
    print(f"Result type: {type(result)}")
    print(f"Result attributes: {dir(result)}")
    if hasattr(result, 'agent'):
        print(f"result.agent: {result.agent}")
    else:
        print("result.agent NOT FOUND")
        
    # Check for other potential attributes
    for attr in ['active_agent', 'last_agent', 'current_agent']:
        if hasattr(result, attr):
            print(f"result.{attr}: {getattr(result, attr)}")

if __name__ == "__main__":
    asyncio.run(debug())
