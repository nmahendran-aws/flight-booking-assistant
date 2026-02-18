import os
import sys
import json
from dotenv import load_dotenv
import asyncio
import os
import sys
from datetime import date
from typing import Any, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool
from langchain_core.tools import tool

# MCP Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from contextlib import AsyncExitStack

class AirlineAgent:
    def __init__(self):
        load_dotenv()
        self.llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
        self.messages: list[BaseMessage] = []
        self.exit_stack = AsyncExitStack()
        self.session = None
        self.langchain_tools = []
        self.llm_with_tools = None
        
        # System Prompt logic (kept same)
        current_date = date.today()
        self.system_message = SystemMessage(content=f"""You are a helpful airline booking assistant. 
        You have access to flight search tools via an MCP Server.
        
        The current date is {current_date}. 
        
        **CRITICAL RULES:**
        1. **Do NOT make assumptions.** You must ask the user for specific details before searching.
        2. **Collect the following Search Details:**
           - **Trip Type**: One-way or Round Trip?
           - **Dates**: Departure Date (and Return Date if Round Trip).
           - **Passengers**: 
             - Number of Adults.
             - Number of Children (ask for ages to categorize them as Children 2-11 or Infants <2).
           - **Class**: Economy, Business, etc. (Optional, default to Economy).
        3. **Collect Booking Details** (After selecting a flight):
           - **Passenger Names**: Full names for EACH passenger (must match the count).
           - **Contact Info**: Email or Phone (if needed for booking).
        4. **FINAL STEP**: Once you have the Flight choice (Number 1, 2, etc.), Passenger Names, and Email, call the `book_flight` tool.
           - Pass the `flight_index` as an integer (e.g., 1 for the first option).
           - The tool will return a **Booking Link**. Provide this link to the user to complete their purchase.
        
        **Process:**
        1. Ask clarifying questions until you have all Search Details.
        2. Call `search_flights` with the specific parameters (count adults, children, etc. based on ages).
        3. Present results clearly (numbered 1, 2, 3...).
        4. If the user wants to book, ask for Passenger Names and Email.
        5. Call `book_flight` with the Flight Number (index) and details.
        
        Do not make up flight data. Use the tools.
        """)
        self.messages.append(self.system_message)

    async def start(self):
        """Initialize connection to MCP Server."""
        if self.session:
             return

        server_script = os.path.join(os.path.dirname(__file__), "server.py")
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_script],
            env=os.environ.copy()
        )
        
        print(f"Connecting to MCP Server at: {server_script}...")
        
        # Enter contexts
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.read, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.read, self.write))
        
        await self.session.initialize()
        
        # Discover tools
        mcp_tools_list = await self.session.list_tools()
        print(f"Connected. Found tools: {[t.name for t in mcp_tools_list.tools]}")
        
        # Bind tools
        self.langchain_tools = []
        for tool_info in mcp_tools_list.tools:
            async def _create_tool_wrapper(t_name=tool_info.name):
                 async def _wrapper(**kwargs):
                     result = await self.session.call_tool(t_name, arguments=kwargs)
                     text_output = []
                     for content in result.content:
                         if content.type == "text":
                             text_output.append(content.text)
                     return "\n".join(text_output)
                 return _wrapper

            wrapper = await _create_tool_wrapper()
            
            lc_tool = StructuredTool.from_function(
                func=None,
                coroutine=wrapper,
                name=tool_info.name,
                description=tool_info.description or "No description",
            )
            self.langchain_tools.append(lc_tool)
            
        self.llm_with_tools = self.llm.bind_tools(self.langchain_tools)

    async def run_loop(self, user_input: str):
        """Process a single user turn."""
        if not self.session:
            await self.start()
            
        self.messages.append(HumanMessage(content=user_input))
        
        final_response = None
        max_iterations = 5
        
        for _ in range(max_iterations):
            print("Invoking LLM...")
            try:
                response = await self.llm_with_tools.ainvoke(self.messages)
            except Exception as e:
                return f"LLM Error: {e}"

            self.messages.append(response)
            
            if not response.tool_calls:
                final_response = response.content
                break
            
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_id = tool_call['id']
                
                print(f"Executing tool: {tool_name} with args: {tool_args}")
                
                selected_tool = next((t for t in self.langchain_tools if t.name == tool_name), None)
                
                tool_output = "Error: Tool not found locally"
                if selected_tool:
                    try:
                        tool_output = await selected_tool.coroutine(**tool_args)
                    except Exception as e:
                        tool_output = f"Tool execution failed: {e}"
                
                self.messages.append(ToolMessage(
                    content=str(tool_output),
                    tool_call_id=tool_id
                ))

        return final_response

    async def close(self):
        """Cleanup connection."""
        await self.exit_stack.aclose()
        self.session = None
