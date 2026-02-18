import asyncio
import sys
import os

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import AirlineAgent

async def main():
    print("Initializing Agent (Async MCP Client)...")
    try:
        agent = AirlineAgent()
        print("Agent initialized.")
        
        # Complex Query
        query = "Find me a round trip flight from SFO to JFK, leaving May 1st 2026 and returning May 10th 2026, for 2 adults and 1 child (age 5)."
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
