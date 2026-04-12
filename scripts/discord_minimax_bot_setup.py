#!/usr/bin/env python3
"""
discord_minimax_bot_setup.py
Discord bot creation for Minimax.
"""
import sys
sys.path.insert(0, '/Users/hagios/Documents/Hagios 1/workspace/scripts')

from playwright.sync_api import sync_playwright

BOT_NAME = "Hagios Minimax"

def get_dialog_text(page):
    dialog = page.query_selector('[role="dialog"]:visible')
    if not dialog:
        return ""
    return dialog.inner_text()

def is_welcome_modal(page):
    return "Welcome to the Developer Portal" in get_dialog_text(page)

def close_welcome_modal(page):
    if not is_welcome_modal(page):
        return
    btn = page.query_selector('button[aria-label="Close"]')
    if btn and btn.is_visible():
        btn.click(force=True)
        page.wait_for_timeout(1500)
        return
    page.keyboard.press("Escape")
    page.wait_for_timeout(1500)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--window-size=1280,900"])
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        print("[STEP 1] Navigating to Discord Developer Portal...")
        page.goto("https://discord.com/developers/applications")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        print(f"  URL: {page.url}")

        if "/login" in page.url:
            print("[STEP 2] Login redirect — waiting for user to complete login...")
            page.wait_for_url("**/developers/applications**", timeout=300000)
            page.wait_for_timeout(3000)

        if is_welcome_modal(page):
            print("[STEP 2b] Closing welcome modal...")
            close_welcome_modal(page)
            page.wait_for_timeout(1000)

        print(f"  Ready at: {page.url}")

        # === Click New Application ===
        page.wait_for_timeout(1000)
        print("[STEP 3] Clicking 'New Application'...")
        new_app = page.get_by_text("New Application", exact=False)
        if new_app:
            new_app.first.click(force=True)
            print("  Clicked.")
        page.wait_for_timeout(3000)

        # If welcome modal appeared, close it and wait for create dialog
        if is_welcome_modal(page):
            print("  Welcome modal appeared — closing...")
            close_welcome_modal(page)
            page.wait_for_timeout(2000)

        # === Fill name input ===
        print("[STEP 4] Looking for name input in create-dialog...")

        inputs = page.query_selector_all('input[type="text"]')
        print(f"  Found {len(inputs)} text inputs total.")
        for inp in inputs:
            ph = inp.get_attribute('placeholder') or ''
            vis = inp.is_visible()
            try:
                parent = inp.evaluate(
                    'el => el.closest("[role=dialog]") ? el.closest("[role=dialog]").innerText : ""'
                )
                in_welcome = "Welcome to the Developer Portal" in parent
            except Exception:
                in_welcome = False
            print(f"    ph='{ph}', vis={vis}, inWelcome={in_welcome}")

        # Fill the first visible input NOT inside welcome modal
        filled = False
        for inp in inputs:
            if not inp.is_visible():
                continue
            try:
                parent = inp.evaluate(
                    'el => el.closest("[role=dialog]") ? el.closest("[role=dialog]").innerText : ""'
                )
                in_welcome = "Welcome to the Developer Portal" in parent
            except Exception:
                in_welcome = False
            if in_welcome:
                continue
            print("  Typing into create-dialog input...")
            inp.click(force=True)
            page.wait_for_timeout(300)
            page.keyboard.type(BOT_NAME, delay=50)
            page.wait_for_timeout(500)
            filled = True
            break

        if not filled:
            print("  Could not fill input. Taking screenshot...")
            page.screenshot(path="/tmp/discord_fill.png")
            print("  Waiting 60s for manual handling...")
            page.wait_for_timeout(60000)
            return

        # === Submit create dialog ===
        print("[STEP 5] Submitting create dialog...")
        page.wait_for_timeout(500)
        result = page.evaluate("""
        () => {
            const dialogs = document.querySelectorAll('[role="dialog"]');
            for (const d of dialogs) {
                if (d.innerText.includes('Welcome to the Developer Portal')) continue;
                const btns = d.querySelectorAll('button');
                for (const b of btns) {
                    if (b.textContent.trim() === 'Create') {
                        b.click();
                        return 'clicked Create';
                    }
                }
            }
            return 'not found';
        }
        """)
        if "clicked Create" not in result:
            print(f"  JS click failed ({result}) — pressing Enter...")
            page.keyboard.press("Enter")
        else:
            print(f"  {result}")
        page.wait_for_timeout(4000)
        print(f"  URL after create: {page.url}")

        # === Navigate to Bot settings ===
        print("[STEP 6] Navigating to Bot settings...")
        page.wait_for_timeout(2000)

        if "/applications/" in page.url and "/bot" not in page.url:
            page.goto(page.url.rstrip("/") + "/bot")
        elif "/applications/" not in page.url:
            page.goto("https://discord.com/developers/applications")
            page.wait_for_timeout(2000)
            if is_welcome_modal(page):
                close_welcome_modal(page)
            try:
                app_item = page.get_by_text(BOT_NAME, exact=False)
                if app_item:
                    app_item.first.click()
                    page.wait_for_timeout(3000)
            except Exception:
                pass
            if "/bot" not in page.url:
                page.goto("https://discord.com/developers/applications")

        page.wait_for_timeout(2000)
        print(f"  Bot settings URL: {page.url}")

        # === Enable MESSAGE CONTENT INTENT ===
        print("[STEP 7] Toggling MESSAGE CONTENT INTENT...")
        page.wait_for_timeout(1000)
        result = page.evaluate("""
        () => {
            const rows = document.querySelectorAll('[class*="item"], [class*="row"]');
            for (const row of rows) {
                if (row.textContent.includes('MESSAGE CONTENT INTENT')) {
                    const cb = row.querySelector('input[type="checkbox"]');
                    if (cb) {
                        if (!cb.checked) { cb.click(); return 'toggled ON'; }
                        return 'already ON';
                    }
                    return 'no checkbox';
                }
            }
            return 'not found on page';
        }
        """)
        print(f"  Result: {result}")

        # Final
        page.screenshot(path="/tmp/discord_final.png")
        print(f"\n[FINAL] {page.url} | /tmp/discord_final.png")
        print("\n[MANUAL] Copy: Bot Token (Reset Token), App ID (General Info), OAuth2 invite URL.")
        print("Then I'll configure OpenClaw Discord integration at localhost:18789")
        try:
            page.context.wait_for_event("close", timeout=600000)
        except Exception:
            pass
        browser.close()
        print("[EXIT]")

if __name__ == "__main__":
    run()
