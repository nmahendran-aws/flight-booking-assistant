import sys
import os

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import AirlineAgent

def verify_agent():
    print("Initializing Agent...")
    try:
        agent = AirlineAgent()
        print("Agent initialized.")
        
        query = "Find me a flight from SFO to JFK on 2026-05-01"
        print(f"Running query: {query}")
        
        response = agent.run(query)
        print("Agent Response:")
        print(response)
        
        agent.close()
        
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_agent()
