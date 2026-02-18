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

            flight_summary = []
            for i, flight in enumerate(all_flights[:5]): # Limit to top 5 for brevity
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

    def book_flight(self, flight_id: str, passenger_names: list[str], email: str) -> str:
        """
        Simulate booking a flight.
        args:
            flight_id: The ID or description of the flight to book.
            passenger_names: List of full names for each passenger.
            email: Contact email address.
        """
        import random
        import string
        
        # Simulate processing time
        print(f"Booking flight {flight_id} for {passenger_names} ({email})...")
        
        # Generate fake confirmation code
        confirmation_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        return f"""
        # Booking Confirmed!
        **Confirmation Code:** {confirmation_code}
        
        **Flight:** {flight_id}
        **Passengers:** {", ".join(passenger_names)}
        **Contact:** {email}
        
        *This is a mock booking. No card was charged.*
        """
