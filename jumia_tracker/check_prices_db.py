import os
import africastalking
import database
import scraper

# ============================================================
# CONFIG
# Load Africa's Talking credentials from config.txt
# Same pattern as your original check_prices.py
# Credentials never hardcoded — always in config file
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Read credentials from environment variables (Render)
# or config.txt (local development)
AT_USERNAME = os.environ.get("AT_USERNAME")
AT_API_KEY  = os.environ.get("AT_API_KEY")
PHONE       = os.environ.get("PHONE")

if not AT_USERNAME:
    config = {}
    config_path = os.path.join(BASE_DIR, "config.txt")
    with open(config_path, "r") as cf:
        for line in cf:
            if ": " in line:
                key, value = line.strip().split(": ", 1)
                config[key] = value
    AT_USERNAME = config["AT_USERNAME"]
    AT_API_KEY  = config["AT_API_KEY"]
    PHONE       = config["PHONE"]

africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms = africastalking.SMS

def send_sms(message, phone):
    try:
        sms.send(message, [phone])
        print(f"SMS sent to {phone}")
    except Exception as e:
        print(f"SMS failed: {e}")


# ============================================================
# MAIN PRICE CHECK LOOP
# ============================================================

def check_all_prices():
    print("Starting price check for all tracked products...")

    # Get every product from the database
    # Skips placeholders — only checks real products
    products = database.get_all_products()

    if not products:
        print("No products being tracked.")
        return

    for product in products:
        product_id   = product['id']
        product_name = product['name']
        url          = product['url']
        username     = product['username']

        print(f"\nChecking: {product_name} for {username}")

        # Get the last recorded price from price_history
        last_price = database.get_last_price(product_id)

        if last_price is None:
            print(f"No price history found for {product_name} — skipping.")
            continue

        # Scrape the current price from Jumia
        scraped = scraper.scrape(url)

        if scraped is None:
            print(f"Scrape failed for {product_name} — skipping.")
            continue

        current_price = scraped['price']
        current_name  = scraped['name']

        print(f"Last price: GHS {last_price} → Current price: GHS {current_price}")

        # Always record the new price in history
        # Even if unchanged — builds a complete price timeline
        database.add_price_history(product_id, current_price)

        # Always update the product's current price
        database.update_product(product_id, current_name, current_price)

        # Only send SMS if price actually changed
        # config["PHONE"] is the admin/test number from config.txt
        # Phase 8: each user will have their own phone number in the users table
        # Get the user's phone from the database row
        # Falls back to config["PHONE"] if user has no phone set yet
        # This handles existing users who signed up before phone was added
       # sqlite3.Row uses index access, not .get()
        # dict() converts the Row to a real dictionary first
        # then .get() works safely — returns None if phone column is empty
        user_phone = dict(product).get('phone') or config["PHONE"]

        if current_price < last_price:
            diff = last_price - current_price
            message = (
                f"PRICE DROPPED!\n"
                f"{product_name}\n"
                f"GHS {last_price} → GHS {current_price}\n"
                f"You save GHS {diff:.2f}\n"
                f"{url}"
            )
            print(message)
            send_sms(message, user_phone)

        elif current_price > last_price:
            diff = current_price - last_price
            message = (
                f"PRICE INCREASED!\n"
                f"{product_name}\n"
                f"GHS {last_price} → GHS {current_price}\n"
                f"Up by GHS {diff:.2f}\n"
                f"{url}"
            )
            print(message)
            send_sms(message, user_phone)

        else:
            print(f"Price unchanged — {product_name}")

    print("\nPrice check complete.")


if __name__ == "__main__":
    check_all_prices()