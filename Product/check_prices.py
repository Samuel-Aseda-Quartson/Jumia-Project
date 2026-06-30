import os
import africastalking
from playwright.sync_api import sync_playwright
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#__files__ holds the paht of the current script
#abspath converts it to a full absolute path
#dirname strips the filename leaving only home/oluwa/JUMIA PROJECT

# --- Load config ---
config = {} #this create a py mean dictinary to hold the config values like a table
config_path = os.path.join(BASE_DIR, "config.txt")
with open(config_path, "r") as cf:
    for line in cf:
        if ": " in line:
            key, value = line.strip().split(": ", 1)
            config[key] = value

# --- Initialize Africa's Talking ---
#these line of code authenicates the session with AT
africastalking.initialize(config["AT_USERNAME"], config["AT_API_KEY"])
sms = africastalking.SMS

#without the try/except block,id AT's api, number or credit is down, 
#the failure will be logged instead of crashing the program.
def send_sms(message):
    try:
        sms.send(message, [config["PHONE"]])
        print("SMS sent!")
    except Exception as e: #exception is an in-built class that catches errors
        print("SMS failed:", e) #as e help us know what failed. e can be any var name.

# --- Load product files ---
files = os.listdir(BASE_DIR)
product_files = [f for f in files if f.startswith("product_") and f.endswith(".txt")] #this is a list comprehension
#it is a compact way to write a loop that creates a list.

if not product_files:
    print("No products being tracked.")
    exit()

# --- One browser for all products ---
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
        #This specific one tells Chromium to hide the signal
        #  that says "I was launched by automation software."
    )

    for file in product_files:
        filepath = os.path.join(BASE_DIR, file)
        product_file = open(filepath, "r", encoding="utf-8")
        data = product_file.read()
        product_file.close()

        lines = data.split("\n")
        product_name = ""
        old_price = None
        url_only = ""

        for line in lines:
            if line.startswith("Name: "):
                product_name = line.replace("Name: ", "")
            if line.startswith("Price: "):
                price_only = line.replace("Price: ", "").replace("GH₵", "").strip()
                old_price = int(float(price_only))
            if line.startswith("URL: "):
                url_only = line.replace("URL: ", "").strip()

        print()
        print("Checking:", product_name)

        page = browser.new_page()
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        try:
            page.goto(url_only, timeout=30000)
        except Exception:
            print("Page load timed out, skipping.")
            page.close()
            continue

        html = page.content()
        page.close()

        parts = html.split('"rawPrice":"')
        if len(parts) <= 1:
            print("Price not found, skipping.")
            continue

        raw_price = parts[1].split('"')[0]
        current_price = int(float(raw_price))
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        #datetime module grabs time and dte from my system clock
        #strftime formats it to a string like 2024-06-30 14:45

        if current_price < old_price:
            diff = old_price - current_price
            msg = (
                f"PRICE DROPPED!\n"
                f"{product_name}\n"
                f"GH₵{old_price} → GH₵{current_price}\n"
                f"You save GH₵{diff}\n"
                f"{url_only}"
            )
            print(msg)
            send_sms(msg)

        elif current_price > old_price:
            diff = current_price - old_price
            msg = (
                f"PRICE INCREASED!\n"
                f"{product_name}\n"
                f"GH₵{old_price} → GH₵{current_price}\n"
                f"Up by GH₵{diff}\n"
                f"{url_only}"
            )
            print(msg)
            send_sms(msg)

        else:
            print("PRICE UNCHANGED —", product_name)

        # Update file with new price and timestamp
        update_file = open(filepath, "w", encoding="utf-8")
        update_file.write("Name: " + product_name + "\n")
        update_file.write("Price: GH₵ " + str(current_price) + "\n")
        update_file.write("URL: " + url_only + "\n")
        update_file.write("Last Checked: " + now + "\n")
        update_file.close()
        print("Updated:", file)

    browser.close()