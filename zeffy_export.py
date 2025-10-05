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
import json
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

# Auto-detect environment
if os.name == 'nt':  # Windows
    DOWNLOAD_FOLDER = os.getenv('DOWNLOAD_FOLDER', r'C:\Users\erin\Zeffy_Exports')
    COOKIE_FILE = r'C:\Users\erin\CFL Member Dashboard\zeffy_cookies.json'
else:  # Linux/Server
    DOWNLOAD_FOLDER = os.getenv('DOWNLOAD_FOLDER', '/var/www/cfl-member-dashboard/exports')
    COOKIE_FILE = '/var/www/cfl-member-dashboard/zeffy_cookies.json'

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

        # Load saved cookies if they exist
        cookie_path = Path(COOKIE_FILE)
        storage_state = None
        if cookie_path.exists():
            print(f"✓ Loading saved cookies from {cookie_path}")
            with open(cookie_path, 'r') as f:
                cookies = json.load(f)
                storage_state = {'cookies': cookies, 'origins': []}
        else:
            print(f"⚠ No saved cookies found. Run save_zeffy_cookies.py first!")

        # Create browser context with download path and realistic user agent
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            storage_state=storage_state
        )

        page = await context.new_page()

        try:
            # If we have cookies, skip login and go straight to payments page
            if storage_state:
                print("Using saved session, skipping login...")
                await page.goto(ZEFFY_PAYMENTS_URL, wait_until='domcontentloaded', timeout=60000)
                await page.wait_for_timeout(3000)

                # Remove date filter to show all historical data
                print("Removing date filter to show all data...")
                try:
                    # Click the "Clear" button to remove date filters
                    await page.click('button:has-text("Clear")', timeout=3000)
                    print("✓ Cleared date filter")
                    await page.wait_for_timeout(3000)  # Wait for page to reload with all data
                except Exception as e:
                    print(f"⚠ Could not clear date filter: {e}")
                    print("Trying alternative method...")
                    try:
                        # Alternative: click the date dropdown and select a wide range
                        await page.click('button:has-text("Add a date range"), input[placeholder*="date"]', timeout=2000)
                        await page.wait_for_timeout(500)
                        # Try to select "2024" or earlier year
                        await page.click('button:has-text("2024")', timeout=2000)
                        print("✓ Selected 2024 data")
                        await page.wait_for_timeout(2000)
                    except:
                        print("⚠ Could not modify date filter, exporting visible data only")
            else:
                # Step 1: Navigate to login page
                print("Navigating to login page...")
                await page.goto(ZEFFY_LOGIN_URL, wait_until='networkidle')
                await page.wait_for_timeout(2000)  # Wait for page to settle

                # Dismiss cookie consent popup if it appears
                print("Checking for cookie popup...")
                try:
                    cookie_accept_selectors = [
                        'button:has-text("Accept all cookies")',
                        'button:has-text("Accept")',
                        'button[id*="cookie"]',
                    ]
                    for selector in cookie_accept_selectors:
                        try:
                            await page.click(selector, timeout=2000)
                            print("✓ Dismissed cookie popup")
                            await page.wait_for_timeout(1000)
                            break
                        except:
                            continue
                except:
                    print("No cookie popup found, continuing...")

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
                await page.wait_for_timeout(3000)

                # Debug screenshot after clicking Next
                await page.screenshot(path='/var/www/cfl-member-dashboard/exports/after_next.png')

                # Find and fill password field on next screen
                print("Entering password...")
                password_selector = 'input[type="password"], input[name="password"], input[id*="password"]'

                # Try to wait for password field with better error handling
                try:
                    await page.wait_for_selector(password_selector, timeout=10000)
                    await page.fill(password_selector, ZEFFY_PASSWORD)
                except:
                    # Take screenshot if password field not found
                    await page.screenshot(path='/var/www/cfl-member-dashboard/exports/password_not_found.png')
                    raise Exception("Password field not found. Check after_next.png and password_not_found.png")

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

            # Step 4: Click Export button - try multiple selectors
            print("Clicking Export button...")
            export_button_selectors = [
                'button:has-text("Export")',
                'button[aria-label*="Export"]',
                'button:text-is("Export")',
                '[data-testid*="export"]',
                'button:text("Export")',
            ]

            export_clicked = False
            for selector in export_button_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.click(selector)
                    export_clicked = True
                    print(f"✓ Clicked export button using selector: {selector}")
                    break
                except:
                    continue

            if not export_clicked:
                # Take screenshot for debugging
                await page.screenshot(path='/var/www/cfl-member-dashboard/exports/debug_screenshot.png')
                raise Exception("Could not find Export button. Screenshot saved to exports/debug_screenshot.png")

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

            # Step 6: Select date range - try to select "All time" or maximum range
            print("Setting date range to All time...")
            date_range_selectors = [
                'button:has-text("All time")',
                'select[name*="date"]',
                '[data-testid*="date-range"]',
            ]

            for selector in date_range_selectors:
                try:
                    await page.click(selector, timeout=2000)
                    await page.wait_for_timeout(500)
                    # Try to click "All time" option if dropdown appeared
                    try:
                        await page.click('button:has-text("All time"), li:has-text("All time")', timeout=2000)
                    except:
                        pass
                    print("✓ Set date range")
                    break
                except:
                    continue

            # Step 7: Click "Select all" checkbox
            print("Clicking Select all...")
            select_all_selector = 'label:has-text("Select all")'
            await page.wait_for_selector(select_all_selector, timeout=5000)

            # Take screenshot before clicking Select all
            await page.screenshot(path='/var/www/cfl-member-dashboard/exports/before_select_all.png')
            print("📸 Screenshot saved: before_select_all.png")

            await page.click(select_all_selector)
            await page.wait_for_timeout(1000)

            # Take screenshot after clicking Select all
            await page.screenshot(path='/var/www/cfl-member-dashboard/exports/after_select_all.png')
            print("📸 Screenshot saved: after_select_all.png")

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
