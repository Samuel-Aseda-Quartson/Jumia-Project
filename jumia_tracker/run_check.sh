#!/bin/bash

# Jumia Price Tracker — Automated Price Check Script
# Runs check_prices_db.py using the project virtual environment
# No Xvfb needed — scraper now runs headless=True

# Activate virtual environment and run the price checker
/home/oluwa/Project/Jumia\ Project/jumia_tracker/.venv/bin/python3 \
"/home/oluwa/Project/Jumia Project/jumia_tracker/check_prices_db.py"
