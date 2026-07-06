from playwright.sync_api import sync_playwright


def scrape(url):
    """
    Takes a Jumia product URL.
    Returns a dictionary with name and price if successful.
    Returns None if scraping fails for any reason.

    This function owns one responsibility — visit Jumia and extract data.
    It does not save anything. It does not call Flask. It just scrapes.
    Separation of concerns — the route coordinates, this function executes.
    """

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                # headless=True → no visible browser window
                # Flask runs as a web server — no screen to show a browser on
                # Phase 4 used Xvfb to fake a display for headless=False
                # headless=True skips that requirement entirely
                args=["--disable-blink-features=AutomationControlled"]
                # Hides the automation signal from Jumia's bot detection
                # Proven working from your Phase 1 and Phase 4 code
            )

            page = browser.new_page()

            # Set User-Agent — proven necessary from check_prices.py
            # Without this, Jumia may serve a different page or block the request
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })

            # Navigate to the product page
            # timeout=30000 → wait maximum 30 seconds before giving up
            # Same value used in check_prices.py — proven safe for Jumia Ghana
            try:
                page.goto(url, timeout=30000)
            except Exception:
                # Page load timed out — network issue or bad URL
                # Return None so the route can handle it gracefully
                print(f"SCRAPER: Page load timed out for {url}")
                browser.close()
                return None

            # Extract product name from page title
            # Proven working from add_product.py
            product_name = page.title()

            # Extract raw HTML
            html = page.content()

            browser.close()

            # Extract price using the proven split pattern from your Phase 1 code
            # Jumia embeds price in JSON inside the page HTML as "rawPrice":"3500.00"
            # Splitting on that string gives us the price value directly
            parts = html.split('"rawPrice":"')

            if len(parts) <= 1:
                # rawPrice not found in HTML
                # Could mean: wrong page, sold out, or Jumia changed their HTML structure
                print(f"SCRAPER: Price not found for {url}")
                return None

            raw_price = parts[1].split('"')[0]
            # parts[1] gives everything after the first "rawPrice":"
            # .split('"')[0] cuts off at the closing quote
            # e.g. '3500.00","something...' → '3500.00'

            price = float(raw_price)
            # float() converts the string "3500.00" to a number 3500.0
            # We store as float in SQLite's REAL column — matches our schema

            # Return a clean dictionary
            # The route unpacks this — it does not care how we got it
            return {
                "name": product_name,
                "price": price
            }

    except Exception as e:
        # Catch-all for any unexpected Playwright errors
        # Log it so you can debug — but never crash Flask
        print(f"SCRAPER: Unexpected error — {e}")
        return None