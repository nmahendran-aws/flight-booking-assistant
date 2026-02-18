from playwright.sync_api import sync_playwright, Page, Browser
import time
from typing import List, Dict, Optional

class GoogleFlights:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def start(self):
        """Starts the browser session."""
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
    
    def stop(self):
        """Stops the browser session."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def search_flights(self, origin: str, destination: str, date: str):
        """
        Searches for flights on Google Flights.
        origin: City or Airport code (e.g., "SFO")
        destination: City or Airport code (e.g., "JFK")
        date: Date in YYYY-MM-DD format (e.g., "2024-12-25")
        """
        if not self.page:
            self.start()
        
        # Use URL parameters for robust and reliable navigation
        # This bypasses the flaky UI interactions (clearing inputs, dropdowns, etc.)
        url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{date}"
        print(f"Navigating to: {url}")
        self.page.goto(url)
        
        # Wait for results to load
        # We wait for the 'Best departing flights' header or a known element like the list of flights.
        try:
            print("Waiting for network idle...")
            self.page.wait_for_load_state("networkidle", timeout=10000)
            print("Waiting for flight cards...")
            
            # Try multiple selectors
            selectors = ["li.pIav2d", "div[role='listitem']", ".gws-flights-results__result-item", "div[jsaction*='click']"]
            found_selector = False
            for selector in selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    found_selector = True
                    print(f"Found selector: {selector}")
                    break
                except:
                    continue
            
            if found_selector:
                return "Search successful. Flights found. Please use 'get_flight_results' to see details."
            else:
                 return "Search completed, but no specific flight cards found. Verify date/route."

        except Exception as e:
            print(f"Timed out waiting for list items: {e}")
            return f"Search initiated but timed out waiting for results: {str(e)}"

    def get_flights(self) -> List[Dict]:
        """Scrapes the flight results from the current page."""
        if not self.page:
            return []

        flights = []
        
        # Strategies to find flight cards
        selectors = ["li.pIav2d", "div[role='listitem']", ".gws-flights-results__result-item", "div[jsaction*='click']"]
        cards = []
        for selector in selectors:
            cards = self.page.locator(selector).all()
            if cards:
                print(f"Using selector: {selector}")
                break

        print(f"Found {len(cards)} potential flight cards.")

        for i, card in enumerate(cards):
            # Limit to top results to avoid processing too much trash
            if i > 5: 
                break
            try:
                # Extract text
                text = card.inner_text()
                # Basic cleaning
                text = text.replace("\n", " | ")
                
                # Check if it looks like a flight (has time, price, etc.)
                if "$" in text or "hr" in text:
                    flights.append({"index": i, "details": text})
            except:
                continue
        
        if not flights:
            # Last resort: Get main content functionality to debug
            try:
                # Try to get the main validation text or a summary
                main_element = self.page.locator("main")
                if main_element.count() > 0:
                    main_text = main_element.inner_text()
                    # Clean up excessive newlines
                    main_text = " ".join(main_text.split())
                    flights.append({"index": -1, "details": "Could not parse individual cards. Page content snippet: " + main_text[:1000]})
                else:
                    flights.append({"index": -1, "details": "No flight information found on page."})
            except:
                pass
                
        return flights

    def select_flight(self, index: int):
        """Selects a flight from the results by index."""
        if not self.page:
            return
        
        cards = self.page.locator("div[role='listitem']").all()
        if not cards:
             cards = self.page.locator("li.pIav2d").all()

        if 0 <= index < len(cards):
            print(f"Selecting flight {index}...")
            cards[index].click()
            self.page.wait_for_load_state("networkidle")
            time.sleep(2)
        else:
            print(f"Invalid flight index: {index}")
