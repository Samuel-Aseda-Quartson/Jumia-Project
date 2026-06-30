from playwright.sync_api import sync_playwright
#  requests.get(url) was pretending to be a browser but later
# cloudfare thought it was a bot an stopped me
#fix it with playwright api and chromium to get pass
#from cloudfare

url = input("Enter Jumia URL: ")

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    page.goto(url)

    print(page.title())

    browser.close()