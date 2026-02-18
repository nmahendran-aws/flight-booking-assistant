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
        
        # Scenario: User wants to book a flight
        # We simulate a conversation history to jump straight to booking
        # But for a true test, we should run the interaction loop.
        
        # 1. Search
        query1 = "Find me a one-way flight from SFO to JFK on May 1st 2026 for 1 adult."
        print(f"\nUser: {query1}")
        response1 = await agent.run_loop(query1)
        print(f"Agent: {response1}")
        
        # 2. Book
        query2 = "Book the first flight for John Doe. My email is john@example.com."
        print(f"\nUser: {query2}")
        response2 = await agent.run_loop(query2)
        print(f"Agent: {response2}")
        
        if "Confirmation Code" in response2:
            print("\nSUCCESS: Booking verified!")
        else:
            print("\nFAILURE: Did not find confirmation code.")
        
        agent.close()
        
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
