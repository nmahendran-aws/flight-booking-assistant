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
    def test_search_flights_success(self, MockGoogleSearch):
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

if __name__ == '__main__':
    unittest.main()
