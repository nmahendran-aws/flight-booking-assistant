import os
import sys

# Ensure the root directory is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import AirlineAgent

def main():
    print("Initialize Airline Agent...")
    try:
        agent = AirlineAgent()
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    print("Agent ready. Type 'exit' or 'quit' to stop.")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            print("Agent is thinking...")
            response = agent.run(user_input)
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            
    print("Closing agent...")
    agent.close()

if __name__ == "__main__":
    main()
