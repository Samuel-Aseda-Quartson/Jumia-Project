#!/bin/bash

# Start a fake display so Playwright can open a browser silently
Xvfb :99 -screen 0 1280x720x24 &
XVFB_PID=$!

# Tell every program in this session to use that fake display
export DISPLAY=:99

# Give Xvfb one second to fully initialize before browser launches
sleep 1

# Run check_prices.py using the exact Python inside our virtual environment
/home/oluwa/Jumia\ Project/.venv/bin/python3 "/home/oluwa/Jumia Project/check_prices.py"

# Clean up — kill Xvfb using the PID we saved earlier
kill $XVFB_PID

