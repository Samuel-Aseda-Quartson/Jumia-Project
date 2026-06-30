import os
from playwright.sync_api import sync_playwright

# Always resolve to the folder this script lives in
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

url = input("Enter Jumia URL: ")

files = os.listdir(BASE_DIR)
for file in files:
    if file.startswith("product_") and file.endswith(".txt"):
        filepath = os.path.join(BASE_DIR, file)   # full path, not just filename
        product_file = open(filepath, "r", encoding="utf-8")
        data = product_file.read()
        product_file.close()
        if f"URL: {url}\n" in data:
            print("Product already being tracked")
            exit()

with sync_playwright() as p:
    
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url)
    product_name = page.title()
    html = page.content()
    parts = html.split('"rawPrice":"')
    if len(parts) <= 1:
        print("Price not found")
        browser.close()
        exit()
    price_part = parts[1]
    raw_price = price_part.split('"')[0]
    browser.close()

product_number = 1
filename = os.path.join(BASE_DIR, f"product_{product_number}.txt")
while os.path.exists(filename):
    product_number += 1
    filename = os.path.join(BASE_DIR, f"product_{product_number}.txt")

file = open(filename, "w", encoding="utf-8")
file.write("Name: " + product_name + "\n")
file.write("Price: GH₵ " + str(int(float(raw_price))) + "\n")
file.write("URL: " + url + "\n")
file.close()
print(os.path.basename(filename), "created")