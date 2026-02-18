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

# MCP Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class AirlineAgent:
    def __init__(self):
        load_dotenv()
        self.llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
        self.messages: list[BaseMessage] = []
        
        # System Prompt
        current_date = date.today()
        self.system_message = SystemMessage(content=f"""You are a helpful airline booking assistant. 
        You have access to flight search tools via an MCP Server.
        
        The current date is {current_date}. 
        When the user mentions a date (e.g., "March 9th"), assume they mean the upcoming date relative to today.
        
        Rules:
        1. If the user asks for flights, ALWAYS use the 'search_flights' tool.
        2. Present the results clearly to the user.
        
        Do not make up information. Use the tools to get real data.
        """)
        self.messages.append(self.system_message)

    async def run_loop(self, user_input: str):
        """
        Main async execution loop:
        1. Connects to MCP Server (src/server.py)
        2. Discovers tools
        3. Runs LLM reasoning loop
        """
        # Define server parameters (launching src/server.py as subprocess)
        server_script = os.path.join(os.path.dirname(__file__), "server.py")
        
        # Ensure we run with the same python executable
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_script],
            env=os.environ.copy() # Pass env for API keys
        )

        print(f"Connecting to MCP Server at: {server_script}...")
        
        # Connect to Server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize session
                await session.initialize()
                
                # List available tools from server
                mcp_tools_list = await session.list_tools()
                print(f"Connected. Found tools: {[t.name for t in mcp_tools_list.tools]}")
                
                # Convert MCP tools to LangChain tools
                langchain_tools = []
                for tool_info in mcp_tools_list.tools:
                    # Create a closure to capture tool_name for the callback
                    def create_tool_func(t_name):
                        async def _tool_wrapper(**kwargs):
                            # Call the tool via MCP session
                            result = await session.call_tool(t_name, arguments=kwargs)
                            # Result content is usually a list of TextContent or ImageContent
                            # We extract text for the LLM
                            text_output = []
                            for content in result.content:
                                if content.type == "text":
                                    text_output.append(content.text)
                            return "\n".join(text_output)
                        return _tool_wrapper

                    # Define the StructuredTool
                    lc_tool = StructuredTool.from_function(
                        func=None, # Async only
                        coroutine=create_tool_func(tool_info.name),
                        name=tool_info.name,
                        description=tool_info.description or "No description",
                    )
                    langchain_tools.append(lc_tool)

                # Bind tools to LLM
                llm_with_tools = self.llm.bind_tools(langchain_tools)
                
                # Add user input
                self.messages.append(HumanMessage(content=user_input))
                
                # Execution Flow
                final_response = None
                max_iterations = 5
                
                for _ in range(max_iterations):
                    print("Invoking LLM...")
                    # Async invoke
                    response = await llm_with_tools.ainvoke(self.messages)
                    self.messages.append(response)
                    
                    if not response.tool_calls:
                        final_response = response.content
                        break
                    
                    # Execute Tools
                    for tool_call in response.tool_calls:
                        tool_name = tool_call['name']
                        tool_args = tool_call['args']
                        tool_id = tool_call['id']
                        
                        print(f"Executing tool: {tool_name} with args: {tool_args}")
                        
                        # Find the matching LangChain tool to execute its coroutine
                        selected_tool = next((t for t in langchain_tools if t.name == tool_name), None)
                        
                        tool_output = "Error: Tool not found locally"
                        if selected_tool:
                            try:
                                # Execute the async wrapper we defined above
                                tool_output = await selected_tool.coroutine(**tool_args)
                            except Exception as e:
                                tool_output = f"Tool execution failed: {e}"
                        
                        # Append result
                        self.messages.append(ToolMessage(
                            content=str(tool_output),
                            tool_call_id=tool_id
                        ))

                return final_response

    def close(self):
        """Cleanup if needed."""
        pass
