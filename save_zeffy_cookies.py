#!/usr/bin/env python3
"""
Interactive script to login to Zeffy and save cookies for automation
Run this ONCE to establish a session, then zeffy_export.py can reuse the cookies
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()

ZEFFY_LOGIN_URL = os.getenv('ZEFFY_LOGIN_URL', 'https://www.zeffy.com/login')

# Auto-detect environment
if os.name == 'nt':  # Windows
    COOKIE_FILE = r'C:\Users\erin\CFL Member Dashboard\zeffy_cookies.json'
else:  # Linux/Server
    COOKIE_FILE = '/var/www/cfl-member-dashboard/zeffy_cookies.json'

async def save_cookies():
    """Login to Zeffy in a visible browser and save cookies"""

    print("=" * 60)
    print("Zeffy Cookie Saver - Manual Login Required")
    print("=" * 60)
    print("\nThis will open a browser window.")
    print("Please login to Zeffy manually, then press Enter in this terminal.")
    print()

    async with async_playwright() as p:
        # Launch browser in VISIBLE mode so you can login manually
        browser = await p.chromium.launch(
            headless=False,  # Visible browser
            slow_mo=50  # Slightly slower for easier interaction
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        page = await context.new_page()

        # Navigate to login page
        print(f"Opening Zeffy login page...")
        await page.goto(ZEFFY_LOGIN_URL)

        # Wait for user to login manually
        print("\n" + "=" * 60)
        print("PLEASE LOGIN TO ZEFFY IN THE BROWSER WINDOW")
        print("=" * 60)
        print("\nSteps:")
        print("1. Complete the login (including any captcha)")
        print("2. Wait until you see your dashboard")
        print("3. Come back here and press Enter")
        print()

        input("Press Enter after you've successfully logged in... ")

        # Save cookies
        print("\nSaving cookies...")
        cookies = await context.cookies()

        cookie_file_path = Path(COOKIE_FILE)
        cookie_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(cookie_file_path, 'w') as f:
            json.dump(cookies, f, indent=2)

        print(f"✓ Cookies saved to: {cookie_file_path}")
        print(f"✓ Cookie count: {len(cookies)}")
        print("\nYou can now run zeffy_export.py and it will use these cookies!")
        print("Cookies typically last 30-90 days before you need to re-login.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(save_cookies())
