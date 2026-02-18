import os
import sys
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.tools import tool
from src.browser import GoogleFlights

# Load environment variables
load_dotenv()

class AirlineAgent:
    def __init__(self):
        # Initialize Google Flights browser wrapper
        self.browser = GoogleFlights(headless=False)
        
        # Initialize LLM
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not found in environment variables.")
        
        self.llm = ChatOpenAI(temperature=0, model="gpt-4-turbo-preview")

        # Define Tools as functions for binding
        @tool
        def search_flights(origin: str, destination: str, date: str):
            """Search for flights given origin, destination, and date (YYYY-MM-DD)."""
            return self.browser.search_flights(origin, destination, date)

        @tool
        def get_flight_results():
            """Get the list of available flights after searching. Returns a list of flight options."""
            return self.browser.get_flights()

        @tool
        def select_flight(index: int):
            """Select a specific flight option by index (0-based)."""
            return self.browser.select_flight(index)

        self.tools = [search_flights, get_flight_results, select_flight]
        self.tools_map = {t.name: t for t in self.tools}
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        from datetime import date
        current_date = date.today()
        
        self.system_message = SystemMessage(content=f"""You are a helpful airline booking assistant. 
        You MUST use the provided 'search_flights' tool to find real flight information from Google Flights.
        
        The current date is {current_date}. 
        When the user mentions a date (e.g., "March 9th"), assume they mean the upcoming date relative to today.
        
        Rules:
        1. If the user asks for flights, ALWAYS use the 'search_flights' tool first. Do not say you cannot browse.
        2. Once you get results from 'search_flights', use 'get_flight_results' to extract the details.
        3. Only after getting the results, present them to the user.
        4. If the user selects a flight, use 'select_flight'.
        
        Do not make up information. Use the tools to get real data.
        """)

        self.messages = [self.system_message]

    def run(self, prompt: str):
        """Runs the agent with the given prompt in a loop until a final answer is produced."""
        try:
            # Append user message
            self.messages.append(HumanMessage(content=prompt))
            
            # Agent Loop
            max_iterations = 5
            for _ in range(max_iterations):
                # 1. Invoke LLM
                print("Invoking LLM...")
                response = self.llm_with_tools.invoke(self.messages)
                self.messages.append(response)
                
                # Debug print
                print(f"LLM Response type: {type(response)}")
                print(f"Tool calls: {response.tool_calls}")
                
                # 2. Check for tool calls
                if not response.tool_calls:
                    # Final answer
                    return response.content
                
                # 3. Execute tools
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    print(f"Executing tool: {tool_name} with args: {tool_args}")
                    
                    if tool_name in self.tools_map:
                        tool_func = self.tools_map[tool_name]
                        try:
                            tool_result = tool_func.invoke(tool_args)
                        except Exception as e:
                            tool_result = f"Error: {str(e)}"
                    else:
                        tool_result = f"Error: Tool {tool_name} not found."
                    
                    # Append tool result
                    self.messages.append(ToolMessage(
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                        content=str(tool_result)
                    ))
            
            return "Agent reached maximum iterations without final answer."

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"An error occurred: {str(e)}"

    def close(self):
        """Closes the browser session."""
        self.browser.stop()
