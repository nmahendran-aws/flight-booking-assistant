import os
import sys
import asyncio

# Ensure the root directory is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import AirlineAgent

async def main():
    print("Initialize Airline Agent (MCP Client Mode)...")
    try:
        agent = AirlineAgent()
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    print("Agent ready. Type 'exit' or 'quit' to stop.")
    
    while True:
        try:
            # Note: input() is blocking, but acceptable here as we don't have background tasks
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            print("Agent is thinking...")
            # Await the async run loop
            response = await agent.run_loop(user_input)
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            
    print("Closing agent...")
    agent.close()

if __name__ == "__main__":
    asyncio.run(main())
