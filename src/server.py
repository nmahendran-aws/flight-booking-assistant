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
def search_flights(origin: str, destination: str, date_str: str, 
                  return_date: str = None, 
                  adults: int = 1, 
                  children: int = 0, 
                  infants_on_lap: int = 0, 
                  infants_in_seat: int = 0,
                  travel_class: int = 1) -> str:
    """
    Search for flights using SerpApi.
    
    Args:
        origin: 3-letter IATA code (e.g., "SFO")
        destination: 3-letter IATA code (e.g., "JFK")
        date_str: Departure date (YYYY-MM-DD)
        return_date: Return date (YYYY-MM-DD) for Round Trip. Optional.
        adults: Number of adults (12+). Default 1.
        children: Number of children (2-11). Default 0.
        infants_on_lap: Number of infants under 2 on lap. Default 0.
        infants_in_seat: Number of infants under 2 in seat. Default 0.
        travel_class: 1=Economy, 2=Premium Eco, 3=Business, 4=First. Default 1.
    """
    if not flight_tool:
        return "Error: Server configuration missing SERPAPI_API_KEY."
    
    if len(origin) != 3 or len(destination) != 3:
        return "Error: Origin and Destination must be 3-letter IATA codes."
    
    return flight_tool.search_flights(
        origin=origin, 
        destination=destination, 
        date_str=date_str,
        return_date=return_date,
        adults=adults,
        children=children,
        infants_on_lap=infants_on_lap,
        infants_in_seat=infants_in_seat,
        travel_class=travel_class
    )

@mcp.tool()
def book_flight(flight_index: int, passenger_names: str, email: str) -> str:
    """
    Generate a booking link for a selected flight.
    
    Args:
        flight_index: The number of the flight option (e.g., 1, 2, 3) from the search results.
        passenger_names: Comma-separated full names of all passengers.
        email: Contact email address for the booking.
    """
    if not flight_tool:
        return "Error: Server configuration missing SERPAPI_API_KEY."
    
    # Simple validation
    if "@" not in email:
        return "Error: Invalid email address."
    
    names_list = [n.strip() for n in passenger_names.split(",")]
    
    try:
        return flight_tool.book_flight(flight_index, names_list, email)
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return f"Error executing book_flight: {str(e)}"

if __name__ == "__main__":
    # Standard entry point for MCP
    mcp.run()
