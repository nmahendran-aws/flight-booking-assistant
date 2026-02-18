import sys
import os

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import AirlineAgent

import asyncio

def verify_agent():
    pass # replaced by async main

async def main():
    print("Initializing Agent (Async MCP Client)...")
    try:
        agent = AirlineAgent()
        print("Agent initialized.")
        
        query = "Find me a flight from SFO to JFK on 2026-05-01"
        print(f"Running query: {query}")
        
        # Await the async run loop
        response = await agent.run_loop(query)
        print("Agent Response:")
        print(response)
        
        agent.close()
        
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
