import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api_tools import SerpApiFlights

class TestSerpApiFlights(unittest.TestCase):
    def setUp(self):
        # Allow init without key for testing
        self.flights = SerpApiFlights(api_key="mock_key")

    @patch('src.api_tools.GoogleSearch')
    def test_search_flights_advanced(self, mock_google_search):
        # Mock response
        mock_search_instance = MagicMock()
        mock_google_search.return_value = mock_search_instance
        mock_search_instance.get_dict.return_value = {
            "best_flights": [
                {
                    "flights": [{"airline": "TestAir"}],
                    "price": "$200",
                    "total_duration": "5h",
                    "booking_token": "TOKEN123"
                }
            ]
        }

        # Call with advanced params
        result = self.flights.search_flights(
            origin="SFO", 
            destination="JFK", 
            date_str="2026-05-01",
            return_date="2026-05-10",
            adults=2,
            children=1
        )

        # Verify GoogleSearch was called with correct params
        expected_params = {
            "engine": "google_flights",
            "departure_id": "SFO",
            "arrival_id": "JFK",
            "outbound_date": "2026-05-01",
            "return_date": "2026-05-10",
            "currency": "USD",
            "hl": "en",
            "type": "1", # Round trip
            "adults": 2,
            "children": 1,
            "infants_on_lap": 0,
            "infants_in_seat": 0,
            "travel_class": 1,
            "api_key": "mock_key"
        }
        mock_google_search.assert_called_with(expected_params)
        
        # Verify parsing included the booking token
        self.assertIn("Booking Token Available", result)

    @patch('src.api_tools.GoogleSearch')
    def test_search_flights_basic(self, MockGoogleSearch):
        # Mocking the JSON response from SerpApi
        mock_response = {
            "best_flights": [
                {
                    "price": 100,
                    "total_duration": 120,
                    "flights": [{"airline": "Mock Airline"}],
                    "extensions": ["Nonstop"],
                    "carbon_emissions": {"this_flight": 500}
                }
            ]
        }
        
        # Setup mock behavior
        mock_instance = MockGoogleSearch.return_value
        mock_instance.get_dict.return_value = mock_response

        # Execute
        result = self.flights.search_flights("SFO", "JFK", "2026-05-01")
        
        # Verify
        self.assertIn("Mock Airline", result)
        self.assertIn("Price: 100", result)
        print("\nTest Result (Success Mock):\n" + result)

    @patch('src.api_tools.GoogleSearch')
    def test_search_flights_no_results(self, MockGoogleSearch):
        mock_instance = MockGoogleSearch.return_value
        mock_instance.get_dict.return_value = {"best_flights": [], "other_flights": []}

        result = self.flights.search_flights("XYZ", "ABC", "2026-05-01")
        self.assertIn("No flights found", result)
        print("\nTest Result (No Results Mock):\n" + result)

    def test_book_flight(self):
        result = self.flights.book_flight(
            flight_id="Test Flight 123", 
            passenger_names=["John Doe", "Jane Doe"], 
            email="test@example.com"
        )
        self.assertIn("Booking Confirmed", result)
        self.assertIn("Confirmation Code", result)
        self.assertIn("John Doe", result)
        print("\nTest Result (Booking):\n" + result)

if __name__ == '__main__':
    unittest.main()
