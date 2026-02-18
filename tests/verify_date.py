import sys
import os

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import AirlineAgent

def verify_date():
    print("Initializing Agent...")
    try:
        agent = AirlineAgent()
        print("Agent initialized.")
        
        # Query with ambiguous year
        query = "Find me flights from BWI to Dallas on March 9th"
        print(f"Running query: {query}")
        
        # We capture stdout to check the tool args (since we print them in agent.py)
        # But here we just run it and observe the logs.
        response = agent.run(query)
        print("Agent Response:")
        print(response)
        
        agent.close()
        
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_date()
