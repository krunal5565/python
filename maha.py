from playwright.sync_api import sync_playwright
import easyocr
import time
import json
import traceback


def solve_captcha(captcha_image_bytes):
    """Solve captcha using EasyOCR."""
    try:
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        result = reader.readtext(captcha_image_bytes, detail=0)

        if not result:
            print("EasyOCR did not detect any text.")
            return ""

        text = result[0].replace(" ", "").strip()
        print(f"OCR detected text: '{text}'")
        return text

    except Exception as e:
        print("Exception during OCR:", e)
        traceback.print_exc()
        return ""


def run():
    print("Starting script...")
    debug_payload = {}

    browser = None      # << FIX HERE

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars"
                ]
            )

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            )

            page = context.new_page()

            # Capture console logs
            page.on("console", lambda msg: print(f"Console log: {msg.type}: {msg.text}"))

            # Capture network requests (optional)
            def log_request(route, request):
                print(f"Network request: {request.method} {request.url}")
                route.continue_()

            page.route("**/*", log_request)

            start_url = "https://pay2igr.igrmaharashtra.gov.in/eDisplay/Propertydetails"
            print("Loading page:", start_url)
            page.goto(start_url)
            page.wait_for_load_state("domcontentloaded")
            print("Page loaded.")

            # Scroll to ensure captcha loads
            page.mouse.move(200, 200)
            time.sleep(0.5)
            page.mouse.wheel(0, 500)
            time.sleep(1)

            captcha_selector = "img#captcha-img"
            print("Waiting for captcha image...")

            try:
                page.wait_for_selector(captcha_selector, timeout=15000)
                print("Captcha image found.")
            except Exception as e:
                print("Captcha NOT found within timeout. Taking screenshot.")
                page.screenshot(path="debug_page.png")
                traceback.print_exc()
                return

            captcha_img = page.locator(captcha_selector)
            captcha_bytes = captcha_img.screenshot()
            captcha_img.screenshot(path="captcha_seen.png")
            print("Saved captcha image as captcha_seen.png")

            # Solve captcha
            solved = solve_captcha(captcha_bytes)
            if not solved.strip():
                print("OCR failed to read captcha. Check captcha_seen.png")
                return

            # Ensure captcha hasn't changed
            captcha_img_new_bytes = captcha_img.screenshot()
            if captcha_bytes != captcha_img_new_bytes:
                print("Captcha image refreshed after OCR, aborting.")
                return

            print("Filling form with data...")

            try:
                page.select_option("select[name='years']", "3")
                debug_payload["years"] = "3"
                print("Selected year: 3")

                page.select_option("select[name='district_id']", "23")
                debug_payload["district_id"] = "23"
                print("Selected district_id: 23")

                time.sleep(1)

                page.select_option("select[name='taluka_id']", "14")
                debug_payload["taluka_id"] = "14"
                print("Selected taluka_id: 14")

                time.sleep(1)

                page.select_option("select[name='village_id']", "34")
                debug_payload["village_id"] = "34"
                print("Selected village_id: 34")

                page.select_option("select[name='article_id']", "8")
                debug_payload["article_id"] = "8"
                print("Selected article_id: 8")

                time.sleep(1)

                page.fill("input[name='free_text']", "2001")
                debug_payload["free_text"] = "2001"
                print("Filled free_text with: 2001")

                page.fill("input[name='captcha']", solved)
                debug_payload["captcha"] = solved
                print(f"Filled captcha input with: {solved}")

            except Exception as e:
                print("Error filling form fields:", e)
                traceback.print_exc()
                return

            print("\n===== DEBUG FORM DATA =====")
            for k, v in debug_payload.items():
                print(f"{k} : {v}")
            print("==========================\n")

            # Save debug metadata
            with open("debug_form.json", "w", encoding="utf-8") as f:
                json.dump(debug_payload, f, indent=4)

            print("Submitting form..Krunal")
            try:
                page.click("button[type='submit']")
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception as e:
                print("Error submitting form:", e)
                traceback.print_exc()

            # Screenshots
            page.screenshot(path="before_submit.png")
            page.screenshot(path="after_submit.png")
            page.screenshot(path="after_submit_full.png", full_page=True)

            with open("property_result.html", "w", encoding="utf-8") as f:
                f.write(page.content())

            print("Saved output HTML and screenshots")

        except Exception as e:
            print("Unexpected error in run():", e)
            traceback.print_exc()

        finally:
            print("Closing browser...")
            if browser:       # << FIX HERE
                browser.close()


if __name__ == "__main__":
    run()
