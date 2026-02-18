from serpapi import GoogleSearch
import os
import json
from datetime import datetime, date

class SerpApiFlights:
    """
    Wrapper around SerpApi Google Flights engine.
    Requires SERPAPI_API_KEY environment variable.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        # Initialize the client with the key
        if not self.api_key:
             # Allow initialization without key for testing/mocking, but warn
             print("Warning: SERPAPI_API_KEY not found. Search will fail unless mocked.")

    def search_flights(self, origin: str, destination: str, date_str: str) -> str:
        """
        Search for one-way flights using SerpApi.
        Returns a JSON string summary of the best flights.
        """
        print(f"Searching flights with SerpApi: {origin} -> {destination} on {date_str}")
        
        if not self.api_key:
            return "Error: Missing SERPAPI_API_KEY."

        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": date_str,
            "currency": "USD",
            "hl": "en",
            "type": "2", # One-way
            "api_key": self.api_key
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Check for error
            if "error" in results:
                return f"Error from SerpApi: {results['error']}"

            best_flights = results.get("best_flights", [])
            other_flights = results.get("other_flights", [])
            all_flights = best_flights + other_flights
            
            if not all_flights:
                return "No flights found for this itinerary."

            flight_summary = []
            for i, flight in enumerate(all_flights[:10]): # Limit to top 10
                flight_summary.append(self._parse_flight(i, flight))
            
            return "\n".join(flight_summary)

        except Exception as e:
            return f"Failed to search flights: {str(e)}"

    def _parse_flight(self, index: int, flight_data: dict) -> str:
        """Helper to format a single flight trail."""
        try:
            price = flight_data.get("price", "N/A")
            duration = flight_data.get("total_duration", "N/A")
            
            legs = flight_data.get("flights", [])
            airline_names = []
            for leg in legs:
                airline_names.append(leg.get("airline", "Unknown Airline"))
            
            airline_str = ", ".join(list(set(airline_names)))
            
            # Extensions often contain carbon info or stops summary
            extensions = flight_data.get("extensions", [])
            stops_info = "Nonstop"
            for ext in extensions:
                 if "stop" in ext.lower():
                     stops_info = ext
                     break

            carbon_emissions = flight_data.get("carbon_emissions", {}).get("this_flight", "N/A")
            
            return (f"{index + 1}. **{airline_str}**\n"
                    f"   - Price: {price}\n"
                    f"   - Duration: {duration}\n"
                    f"   - Stops: {stops_info}\n"
                    f"   - CO2: {carbon_emissions} g")
        except Exception as e:
            return f"{index + 1}. [Error parsing flight details]"
