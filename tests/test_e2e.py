# tests/test_sanity.py
import os
from google import genai
from google.genai import types
from appium import webdriver
from appium.options.android import UiAutomator2Options

from drivers.appium_driver import scale_coordinates
from selenium.webdriver.support.ui import WebDriverWait
import time

# 1. Setup Appium for Home Depot App
options = UiAutomator2Options()
options.platform_name = "Android"
options.device_name = "emulator-5544"
options.app_package = "com.thehomedepotca"
options.app_activity = "com.thehomedepotca.view.splash.activity.SplashActivity"
# CRITICAL STABILITY SETTINGS
options.set_capability("appium:noReset", True)            # Don't kill app on start
options.set_capability("appium:autoGrantPermissions", True) # Bypass permission popups
options.set_capability("appium:newCommandTimeout", 300)    # Give Gemini time to think
options.set_capability("appium:adbExecTimeout", 60000)      # Wait longer for ADB
driver = webdriver.Remote("http://localhost:4723", options=options)

# 2. Setup Gemini Client

client = genai.Client(
    api_key="your api key")
model_id = "gemini-2.5-computer-use-preview-10-2025"#"gemini-3-pro-preview"#"gemini-2.5-flash"


def run_automation_step(goal):
    '''''time.sleep(5)

    driver.terminate_app("com.thehomedepotca")
    time.sleep(2)

    driver.activate_app("com.thehomedepotca")

    WebDriverWait(driver, 20).until(
        lambda d: d.current_package == "com.thehomedepotca"
    )'''

    print("Waiting for app to stabilize...")
    time.sleep(8)  # Home Depot splash screen takes a while
    print("Connected to package:", driver.current_package)
    # Take screenshot & get screen size
    screenshot_bytes = driver.get_screenshot_as_png()
    print("Got screenshot")
    # 2. Save to a local file
    with open("debug_screenshot.png", "wb") as f:
        f.write(screenshot_bytes)
    print("Screenshot saved as debug_screenshot.png - check this file!")
    size = driver.get_window_size()
    print(f"size** {size}")


    # Call Gemini with Computer Use Tool
    response = client.models.generate_content(
        model=model_id,
        contents=[
            types.Content(
                role="user",
                parts=[
                    # Some previews require the prompt/goal to be the FIRST part
                    types.Part(text=goal),
                    # Then the image
                    types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png")
                ]
            )
        ],
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        # Stay with BROWSER; it's the only one fully mapped to this model ID
                        environment=types.Environment.ENVIRONMENT_UNSPECIFIED
                    )
                )
            ],
        )
    )
    print(response)
    # 1. Capture the model's request
    # (This is the response you just got)
    model_parts = response.candidates[0].content.parts

    # 2. Prepare the feedback for the model
    response_parts = []
    for part in model_parts:
        if part.function_call:
            call = part.function_call
            print(f"Model requested: {call.name}")

            # If it's the 'open_web_browser', just tell the model it worked!
            if call.name == "open_web_browser":
                response_parts.append(
                    types.Part.from_function_response(
                        name=call.name,
                        response={'result': 'success', 'url': 'app://home_depot'}
                    )
                )

    # 3. Send the response back to continue the loop
    # You MUST include the previous history so the model has context
    new_response = client.models.generate_content(
        model=model_id,
        contents=[
            # History: The user's original goal + screenshot
            types.Content(role="user", parts=[types.Part(text=goal),
                                              types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png")]),
            # History: The model's call to open the browser
            response.candidates[0].content,
            # New: Your "confirmation" that the browser (app) is open
            types.Content(role="user", parts=response_parts)
        ],
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        # Stay with BROWSER; it's the only one fully mapped to this model ID
                        environment=types.Environment.ENVIRONMENT_UNSPECIFIED
                    )
                )
            ],
        )
    )

    print(new_response)
    #print(new_response.candidates[0].content.parts[0].function_call.name)
    # This should now be 'click_at' or 'type_text_at'!
    # Process Action
    # Process Action - Loop through all parts
    for part in new_response.candidates[0].content.parts:
        # 1. Check if the part is text (for logging/debugging)
        if part.text:
            print(f"Model Thought: {part.text}")

        # 2. Check if the part is a function call
        if part.function_call:
            args = part.function_call.args
            action = part.function_call.name
            print(f"Executing Action: {action} with args: {args}")

            if "click_at" in action:
                x, y = scale_coordinates(args['x'], args['y'], size['width'], size['height'])
                driver.tap([(x, y)])
                print(f"Tapped at {x}, {y}")



            elif "type_text_at" in action:

                x, y = scale_coordinates(args['x'], args['y'], size['width'], size['height'])

                # 1. Tap to focus

                driver.tap([(x, y)])

                print(f"Tapped for focus at {x}, {y}")

                time.sleep(2)  # Wait for the new search screen to stabilize

                # 2. Use ADB to type (this is much more stable for layout shifts)

                text_to_type = args['text']

                # We use shell because it bypasses the need for an 'active_element' object

                driver.execute_script('mobile: shell', {

                    'command': 'input',

                    'args': ['text', text_to_type]

                })

                print(f"Typed '{text_to_type}' via ADB shell")

                # 3. Handle Enter/Search

                if args.get('press_enter'):
                    time.sleep(1)

                    # 66 is the Android KeyCode for ENTER

                    driver.execute_script('mobile: shell', {

                        'command': 'input',

                        'args': ['keyevent', '66']

                    })

                    print("Sent Enter keycode 66")


def save_debug_screenshot(screenshot_bytes, turn_count):
    """Saves screenshots to a debug folder for tracking AI progress."""
    folder = "automation_debug"
    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = f"{folder}/step_{turn_count}.png"
    with open(filename, "wb") as f:
        f.write(screenshot_bytes)
    print(f"📸 Screenshot saved: {filename}")


def run_agentic_automation(goal, max_turns=20):
    history = []
    last_action = None

    # We append a 'Format Requirement' to your goal
    enhanced_goal = goal# + " Once finished, provide a final summary including the Price and 'Add to Cart' status in a clear list."

    for turn in range(max_turns):
        turn_id = turn + 1
        screenshot_bytes = driver.get_screenshot_as_png()
        save_debug_screenshot(screenshot_bytes, turn_id)

        size = driver.get_window_size()
        w, h = size['width'], size['height']

        # SELF-CORRECTION LOGIC:
        # If we've been here before, tell Gemini to be careful
        prompt_content = f"Current Step for Goal: {enhanced_goal}"
        if turn > 0:
            prompt_content += "\nObserve the screenshot carefully. If your last action didn't change the screen, try a different element."

        user_part = types.Content(
            role="user",
            parts=[
                types.Part(text=prompt_content),
                types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png")
            ]
        )

        # Only keep the last 2-3 turns of history to prevent token bloat
        # and keep the model's 'eyes' on the current state
        context_history = history[-6:]  # 3 user turns + 3 model turns


        response = client.models.generate_content(
            model='gemini-2.5-computer-use-preview-10-2025',
            contents=context_history + [user_part],
            config=types.GenerateContentConfig(
                tools=[types.Tool(computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_BROWSER
                ))]
            )
        )
        print("******************** RESPONSE *************************************")
        print(response)
        history.append(user_part)
        model_content = response.candidates[0].content
        history.append(model_content)


        found_action = False
        for part in model_content.parts:
            if part.text:
                print(f"🧠 Gemini: {part.text}")

            if part.function_call:
                found_action = True
                action = part.function_call.name
                args = part.function_call.args

                x, y = scale_coordinates(args.get('x', 0), args.get('y', 0), w, h)

                if action == "open_web_browser":
                    print("✅ Action: App Ready")
                elif "click_at" in action:
                    driver.tap([(x, y)])
                    print(f"🖱️ Action: Tap at {x}, {y}")
                elif "type_text_at" in action:
                    driver.tap([(x, y)])
                    time.sleep(1)
                    driver.execute_script('mobile: shell', {'command': 'input', 'args': ['text', args['text']]})
                    if args.get('press_enter'):
                        driver.execute_script('mobile: shell', {'command': 'input', 'args': ['keyevent', '66']})
                    print(f"⌨️ Action: Typed '{args['text']}'")
                elif "scroll_document" in action:
                    direction = args.get('direction', 'down')
                    # Standard mobile swipe: center of screen, move up to scroll down
                    start_x, start_y = w // 2, h // 2
                    end_x, end_y = w // 2, h // 4 if direction == 'down' else h * 3 // 4

                    driver.swipe(start_x, start_y, end_x, end_y, 400)
                    print(f"↕️ Action: Scrolled {direction}")

        # THE STOP CONDITION
        if not found_action:
            print("🏁 No more actions. Asking for final verification...")

            # We must include the same config/tools as the main loop!
            final_check = client.models.generate_content(
                model=model_id,
                contents=history + [types.Part(
                    text="You have stopped performing actions. Please provide a clear final summary for the goal: " + goal
                )],
                config=types.GenerateContentConfig(  # <--- Add this back!
                    tools=[types.Tool(computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER
                    ))]
                )
            )
            print(f"✨ VERIFICATION REPORT: {final_check.text}")
            break

        time.sleep(4)  # Slightly longer wait for Home Depot animations

# Run the test
if __name__ == "__main__":
    goal = "Search for 'hammer', select the first one in the search list, verify that the user is navigate to the product details page, verify price is shown, and check if 'Add to Cart' is visible."
    run_agentic_automation(goal)