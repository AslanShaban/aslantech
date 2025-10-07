import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Go to the application, bypassing login with testing=true
            await page.goto("http://localhost:8000/index.html?testing=true", wait_until="networkidle", timeout=15000)

            # --- Wait for app initialization ---
            # Wait for the custom data attribute signal that the app is ready.
            await expect(page.locator("body")).to_have_attribute("data-app-initialized", "true", timeout=15000)

            # --- 1. Navigate to Sales Tab using JavaScript ---
            await page.evaluate("switchTab('sales')")
            await expect(page.locator("#sales-table")).to_be_visible(timeout=10000)

            # --- 2. Open Add Sale Modal ---
            await page.get_by_role("button", name="إضافة عملية بيع").click()
            await expect(page.locator("#form-modal-title")).to_have_text("تسجيل عملية بيع")

            # --- 3. Fill out the form with cascading selections ---
            await page.locator("#modal-s-type").select_option("product")

            # Select a warehouse - Wait for options to be populated
            await expect(page.locator("#modal-s-warehouse > option[value]")).to_have_count(2, timeout=10000)
            await page.locator("#modal-s-warehouse").select_option(label="المستودع الرئيسي")

            # Select a product category - Wait for it to be populated
            await expect(page.locator("#modal-s-category > option[value]")).to_have_count(2, timeout=5000)
            await page.locator("#modal-s-category").select_option(label="الكترونيات")

            # Select a product - Wait for it to be populated
            await expect(page.locator("#modal-s-product > option:nth-child(2)")).to_be_enabled(timeout=5000)
            await page.locator("#modal-s-product").select_option(label="لابتوب (المتاح: 5)")

            # Verify cost is auto-filled
            await expect(page.locator("#modal-s-cost")).to_have_value("700")

            # Enter sale details
            await page.locator("#modal-s-qty").fill("1")
            await page.locator("#modal-s-price").fill("850")

            # --- 4. Submit the form ---
            await page.locator("#form-modal-submit-btn").click()

            # --- 5. Verify the result ---
            await expect(page.locator("#custom-alert")).to_be_visible()
            await expect(page.locator("#alert-message")).to_have_text("تم تسجيل عملية البيع بنجاح!")
            await page.locator("#alert-ok-btn").click()
            await expect(page.locator("#form-modal")).to_be_hidden()

            # Verify the new sale appears in the table
            new_row = page.locator("#sales-table tr").first
            await expect(new_row.locator("td").nth(2)).to_have_text("لابتوب")
            await expect(new_row.locator("td").nth(4)).to_have_text("1")
            await expect(new_row.locator("td").nth(6)).to_have_text("850.00 د.أ")

            # --- 6. Take a screenshot ---
            await page.screenshot(path="jules-scratch/verification/verification.png")

            print("Verification script completed successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")
            await page.screenshot(path="jules-scratch/verification/error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())