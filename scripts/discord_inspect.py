#!/usr/bin/env python3
"""Inspect Discord Developer Portal modal structure, then wait for input."""
import sys
sys.path.insert(0, '/Users/hagios/Documents/Hagios 1/workspace/scripts')

from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--window-size=1280,900"])
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        print("[*] Navigating to Discord Developer Portal...")
        page.goto("https://discord.com/developers/applications")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        print(f"[*] URL: {page.url}")

        # Click "New Application"
        new_app = page.get_by_text("New Application")
        print(f"[*] Found 'New Application' element: {new_app}")
        new_app.click()
        page.wait_for_timeout(3000)
        print(f"[*] After click URL: {page.url}")

        # Inspect any modal/dialog
        print("\n=== DIALOGS ===")
        for d in page.query_selector_all('[role="dialog"]'):
            if d.is_visible():
                print(f"Visible dialog: {d.inner_text()[:300]}")
                for inp in d.query_selector_all('input'):
                    print(f"  Input: ph={inp.get_attribute('placeholder')}, "
                          f"label={inp.get_attribute('aria-label')}, "
                          f"name={inp.get_attribute('name')}, "
                          f"type={inp.get_attribute('type')}")

        print("\n=== ALL VISIBLE MODALS ===")
        for m in page.query_selector_all('.modalContainer, [class*="modal"]:visible'):
            print(f"Modal: {m.inner_text()[:300]}")

        print("\n=== PAGE BODY TEXT ===")
        print(page.inner_text("body")[:1500])

        print("\n=== SAVING SCREENSHOT ===")
        page.screenshot(path="/tmp/discord_inspect.png")
        print("Screenshot: /tmp/discord_inspect.png")

        print("\n[*] Browser staying open. Type something in this terminal + Enter to close:")
        input()
        browser.close()

if __name__ == "__main__":
    run()
