"""
Zeffy Payment Export Automation Script
======================================
This script automates logging into Zeffy and downloading payment data as CSV.

Requirements:
    pip install playwright python-dotenv
    playwright install chromium

Usage:
    python zeffy_export.py

Troubleshooting:
    If selectors break, use: playwright codegen https://www.zeffy.com/login
    to inspect current element selectors and update them in the script.
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Load environment variables from .env file
load_dotenv()

# Configuration from .env
ZEFFY_EMAIL = os.getenv('ZEFFY_EMAIL')
ZEFFY_PASSWORD = os.getenv('ZEFFY_PASSWORD')
ZEFFY_LOGIN_URL = os.getenv('ZEFFY_LOGIN_URL', 'https://www.zeffy.com/login')
ZEFFY_PAYMENTS_URL = os.getenv('ZEFFY_PAYMENTS_URL', 'https://www.zeffy.com/en-US/o/fundraising/payments')
DOWNLOAD_FOLDER = os.getenv('DOWNLOAD_FOLDER', r'C:\Users\erin\Zeffy_Exports')

# Validate required environment variables
if not ZEFFY_EMAIL or not ZEFFY_PASSWORD:
    raise ValueError("ZEFFY_EMAIL and ZEFFY_PASSWORD must be set in .env file")

async def download_zeffy_payments():
    """Main function to automate Zeffy payment export"""

    # Ensure download folder exists
    download_path = Path(DOWNLOAD_FOLDER)
    download_path.mkdir(parents=True, exist_ok=True)

    print(f"Starting Zeffy export automation...")
    print(f"Download folder: {download_path}")

    async with async_playwright() as p:
        # Launch browser in headless mode (invisible)
        browser = await p.chromium.launch(
            headless=True,  # Set to False for debugging
            downloads_path=str(download_path)
        )

        # Create browser context with download path
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )

        page = await context.new_page()

        try:
            # Step 1: Navigate to login page
            print("Navigating to login page...")
            await page.goto(ZEFFY_LOGIN_URL, wait_until='networkidle')
            await page.wait_for_timeout(2000)  # Wait for page to settle

            # Step 2: Enter credentials and login
            print("Logging in...")

            # Find and fill email field (adjust selector if needed)
            email_selector = 'input[type="email"], input[name="email"], input[id*="email"]'
            await page.wait_for_selector(email_selector, timeout=10000)
            await page.fill(email_selector, ZEFFY_EMAIL)

            # Click Next button after email (not the Google login button)
            print("Clicking Next button...")
            next_button = 'button:has-text("Next")'
            await page.click(next_button)
            await page.wait_for_timeout(2000)

            # Find and fill password field on next screen
            print("Entering password...")
            password_selector = 'input[type="password"], input[name="password"], input[id*="password"]'
            await page.wait_for_selector(password_selector, timeout=10000)
            await page.fill(password_selector, ZEFFY_PASSWORD)

            # Click Confirm button to login
            print("Clicking Confirm button...")
            confirm_button = 'button:has-text("Confirm")'
            await page.click(confirm_button)

            # Wait for navigation after login
            print("Waiting for login to complete...")
            await page.wait_for_load_state('domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)  # Additional wait for dashboard to load

            # Step 3: Navigate to payments page
            print(f"Navigating to payments page...")
            await page.goto(ZEFFY_PAYMENTS_URL, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(5000)  # Wait for page to fully render

            # Step 4: Click Export button
            print("Clicking Export button...")
            export_button_selector = 'button:has-text("Export")'
            await page.wait_for_selector(export_button_selector, timeout=10000)
            await page.click(export_button_selector)

            # Wait for export modal to appear
            await page.wait_for_timeout(1000)

            # Step 5: Ensure "Payments" tab is selected (it should be by default)
            print("Selecting export options...")
            payments_tab_selector = 'button:has-text("Payments")'
            try:
                await page.click(payments_tab_selector, timeout=5000)
            except:
                print("Payments tab already selected or not found, continuing...")

            await page.wait_for_timeout(500)

            # Step 6: Click "Select all" checkbox
            print("Clicking Select all...")
            select_all_selector = 'label:has-text("Select all")'
            await page.wait_for_selector(select_all_selector, timeout=5000)
            await page.click(select_all_selector)
            await page.wait_for_timeout(1000)

            # Step 7: Click the Export button in the modal (inside the dialog)
            print("Starting export...")
            # Use a more specific selector for the Export button within the modal dialog
            modal_export_button = 'div[role="dialog"] button:has-text("Export")'

            # Set up download promise before clicking
            async with page.expect_download(timeout=60000) as download_info:
                await page.click(modal_export_button, force=True)

            download = await download_info.value

            # Step 8: Save the downloaded file with timestamp
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f'zeffy-payments-{timestamp}.csv'
            save_path = download_path / filename

            await download.save_as(save_path)
            print(f"✓ Export successful!")
            print(f"✓ File saved: {save_path}")

            # Optional: Print file size
            file_size = save_path.stat().st_size
            print(f"✓ File size: {file_size:,} bytes")

        except PlaywrightTimeout as e:
            print(f"✗ Timeout error: {e}")
            print("Tip: Run 'playwright codegen https://www.zeffy.com/login' to update selectors")

        except Exception as e:
            print(f"✗ Error occurred: {e}")
            # Take screenshot for debugging
            screenshot_path = download_path / f'error-screenshot-{datetime.now().strftime("%Y%m%d-%H%M%S")}.png'
            await page.screenshot(path=str(screenshot_path))
            print(f"Screenshot saved to: {screenshot_path}")

        finally:
            # Close browser
            await browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(download_zeffy_payments())
