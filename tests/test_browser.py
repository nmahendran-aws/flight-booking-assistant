import sys
import os
import time

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.browser import GoogleFlights

def test_browser():
    print("Testing browser automation...")
    browser = GoogleFlights(headless=False)
    try:
        print("Searching for flights from SFO to JFK on 2026-05-01...")
        browser.search_flights("SFO", "JFK", "2026-05-01")
        print("Search initiated. Waiting for results...")
        
        # Depending on network speed, might need more wait time or better robust waiting in browser.py
        # browser.py waits for networkidle, which is good.
        
        print("Extracting results...")
        flights = browser.get_flights()
        print(f"Found {len(flights)} flights.")
        for i, flight in enumerate(flights):
            print(f"Flight {i}: {flight}")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Closing browser...")
        # Keep open for a moment to see
        time.sleep(2)
        browser.stop()

if __name__ == "__main__":
    test_browser()
