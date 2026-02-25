import os
import time
from google import genai
from google.genai import types
from playwright.sync_api import sync_playwright

# 1. Setup Gemini Client
API_KEY = os.getenv("API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.5-computer-use-preview-10-2025"


# 2. Coordinate Scaling Helper
def scale_coords(gemini_coord, actual_dim):
    """Gemini 0-1000 -> Playwright Pixels"""
    return int((gemini_coord / 1000) * actual_dim)


def run_agentic_web_automation(goal, url, max_turns=15):
    with sync_playwright() as p:
        # Launch Browser (headless=False so you can watch)
        browser = p.chromium.launch(headless=False)
        # Fix viewport for consistent Gemini vision (Recommended: 1280x800)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(url)
        history = []

        for turn in range(max_turns):
            print(f"\n--- Turn {turn + 1} ---")

            # 1. Capture State
            screenshot_bytes = page.screenshot()
            width = page.viewport_size["width"]
            height = page.viewport_size["height"]

            user_part = types.Content(
                role="user",
                parts=[
                    types.Part(text=f"Goal: {goal}"),
                    types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png")
                ]
            )

            # 2. Call Gemini
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=history + [user_part],
                config=types.GenerateContentConfig(
                    tools=[types.Tool(computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER
                    ))]
                )
            )

            history.append(user_part)
            model_content = response.candidates[0].content
            history.append(model_content)

            found_action = False
            for part in model_content.parts:
                if part.text:
                    print(f"🧠 Thought: {part.text}")

                if part.function_call:
                    found_action = True
                    action = part.function_call.name
                    args = part.function_call.args

                    # Convert coordinates
                    x = scale_coords(args.get('x', 0), width)
                    y = scale_coords(args.get('y', 0), height)

                    if action == "click_at":
                        page.mouse.click(x, y)
                        print(f"🖱️ Clicked at {x}, {y}")

                    elif action == "type_text_at":
                        # Playwright click + fill is very reliable
                        page.mouse.click(x, y)
                        page.keyboard.type(args['text'])
                        if args.get('press_enter', True):
                            page.keyboard.press("Enter")
                        print(f"⌨️ Typed: {args['text']}")

                    elif action == "scroll_document":
                        direction = args.get('direction', 'down')
                        scroll_amount = 500 if direction == 'down' else -500
                        page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                        print(f"↕️ Scrolled {direction}")

            if not found_action:
                print("🏁 Goal reached or no more actions.")
                break

            time.sleep(2)  # Brief wait for page stability

        browser.close()


if __name__ == "__main__":
    MY_GOAL = "Search for 'hammer' on Home Depot, click the first result, and find the price."
    run_agentic_web_automation(MY_GOAL, "https://www.homedepot.com")