from mcp.server.fastmcp import FastMCP
import sys
import os

# Ensure project root is in path so we can import src.api_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api_tools import SerpApiFlights
from datetime import date

# Initialize FastMCP server
mcp = FastMCP("Airline Agent")

# Initialize Flight Tool
# Note: We initialize lazily or handle missing key gracefully
flight_tool = None
try:
    if os.getenv("SERPAPI_API_KEY"):
        flight_tool = SerpApiFlights()
    else:
        print("Warning: SERPAPI_API_KEY not found. Flight search will fail.")
except Exception as e:
    print(f"Error initializing SerpApi tool: {e}")


@mcp.tool()
def search_flights(origin: str, destination: str, date_str: str) -> str:
    """
    Search for flights between two airports on a specific date.
    
    Args:
        origin: 3-letter IATA code for departure airport (e.g., "SFO", "JFK")
        destination: 3-letter IATA code for arrival airport
        date_str: Date in YYYY-MM-DD format
    """
    if not flight_tool:
        return "Error: Server configuration missing SERPAPI_API_KEY."
    
    # Simple validation
    if len(origin) != 3 or len(destination) != 3:
        return "Error: Origin and Destination must be 3-letter IATA codes (e.g., SFO, LHR)."
    
    return flight_tool.search_flights(origin, destination, date_str)

if __name__ == "__main__":
    # Standard entry point for MCP
    mcp.run()
