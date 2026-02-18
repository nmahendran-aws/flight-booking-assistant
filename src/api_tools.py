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
        self.last_results = [] # Cache for last search results
        self.last_search_url = "https://www.google.com/travel/flights" # Cache for the search URL
        # Initialize the client with the key
        if not self.api_key:
             # Allow initialization without key for testing/mocking, but warn
             print("Warning: SERPAPI_API_KEY not found. Search will fail unless mocked.")

    def search_flights(self, origin: str, destination: str, date_str: str, 
                      return_date: str = None, 
                      adults: int = 1, 
                      children: int = 0, 
                      infants_on_lap: int = 0, 
                      infants_in_seat: int = 0,
                      travel_class: int = 1) -> str:
        """
        Search for flights using SerpApi.
        args:
            origin: 3-letter IATA code
            destination: 3-letter IATA code
            date_str: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD). If provided, searches Round Trip.
            adults: Number of adults (12+ years). Default 1.
            children: Number of children (2-11 years). Default 0.
            infants_on_lap: Number of infants on lap (under 2). Default 0.
            infants_in_seat: Number of infants in seat (under 2). Default 0.
            travel_class: 1=Economy, 2=Premium Eco, 3=Business, 4=First. Default 1 (Economy).
        """
        trip_type = "2" # Default One-way
        if return_date:
            trip_type = "1" # Round Trip
            print(f"Searching flights: {origin} -> {destination} ({date_str} to {return_date})")
        else:
            print(f"Searching flights: {origin} -> {destination} on {date_str}")
        
        if not self.api_key:
            return "Error: Missing SERPAPI_API_KEY."

        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": date_str,
            "currency": "USD",
            "hl": "en",
            "type": trip_type,
            "adults": adults,
            "children": children,
            "infants_on_lap": infants_on_lap,
            "infants_in_seat": infants_in_seat,
            "travel_class": travel_class,
            "api_key": self.api_key
        }

        if return_date:
            params["return_date"] = return_date

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

            # Update Cache
            self.last_results = all_flights[:10] # Trace top 10
            self.last_search_url = results.get("search_metadata", {}).get("google_flights_url", "https://www.google.com/travel/flights")

            flight_summary = []
            for i, flight in enumerate(all_flights[:5]): # Limit to top 5 for brevity
                flight_summary.append(self._parse_flight(i, flight))
            
            return "\n".join(flight_summary)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Failed to search flights: {str(e)}"

    def _parse_flight(self, index: int, flight_data: dict) -> str:
        """Helper to format a single flight trail."""
        try:
            price = flight_data.get("price", "N/A")
            duration = flight_data.get("total_duration", "N/A")
            
            legs = flight_data.get("flights", [])
            if not legs:
                return f"{index + 1}. [No flight details available]"

            # Times
            first_leg = legs[0]
            last_leg = legs[-1]
            
            dep_time = first_leg.get("departure_airport", {}).get("time", "N/A")
            dep_airport = first_leg.get("departure_airport", {}).get("id", "")
            
            arr_time = last_leg.get("arrival_airport", {}).get("time", "N/A")
            arr_airport = last_leg.get("arrival_airport", {}).get("id", "")
            
            
            airline_names = []
            for leg in legs:
                airline_names.append(leg.get("airline", "Unknown Airline"))
            
            airline_str = ", ".join(list(set(airline_names)))
            
            extensions = flight_data.get("extensions", [])
            stops_info = "Nonstop"
            for ext in extensions:
                 if "stop" in ext.lower():
                     stops_info = ext
                     break

            carbon_emissions = flight_data.get("carbon_emissions", {}).get("this_flight", "N/A")
                
            booking_token = flight_data.get("booking_token", None)
            booking_link_msg = ""
            if booking_token:
                booking_link_msg = f"\n   - [Booking Token Available: {booking_token[:10]}...]"

            return (f"{index + 1}. **{airline_str}**\n"
                    f"   - Price: {price}\n"
                    f"   - Departure: {dep_time} ({dep_airport})\n"
                    f"   - Arrival: {arr_time} ({arr_airport})\n"
                    f"   - Duration: {duration}\n"
                    f"   - Stops: {stops_info}"
                    f"{booking_link_msg}")
        except Exception as e:
            return f"{index + 1}. [Error parsing flight details]"

    def book_flight(self, flight_index: int, passenger_names: list[str], email: str) -> str:
        """
        Generates a booking link for the selected flight.
        args:
            flight_index: The index of the flight (1-based) from the last search results.
            passenger_names: List of full names for each passenger.
            email: Contact email address.
        """
        if not self.last_results:
            return "Error: No search results found. Please search for flights first."
        
        try:
            # Convert 1-based index to 0-based
            idx = int(flight_index) - 1
            if idx < 0 or idx >= len(self.last_results):
                return f"Error: Invalid flight index {flight_index}. Please select a number from the list."
            
            selected_flight = self.last_results[idx]
            
            # Use the captured search URL as the deep link to the results page
            # This allows the user to click the exact flight they found
            deep_link = self.last_search_url
            
            airline = selected_flight.get("flights", [{}])[0].get("airline", "Selected Airline")
            price = selected_flight.get("price", "N/A")
            
            return f"""
            # Booking Link Generated
            
            You selected: **{airline}** ({price})
            
            **Passengers:** {", ".join(passenger_names)}
            **Contact:** {email}
            
            **[Click here to complete your booking on Google Flights]({deep_link})**
            *(Note: This link takes you to the results page. Please select the flight matching {price})*
            """
        except Exception as e:
            return f"Failed to generate booking link: {str(e)}"
