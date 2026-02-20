from google import genai
import PIL.Image

client = genai.Client(api_key="YOUR_API_KEY")


def get_next_action(screenshot_path, goal):
    img = PIL.Image.open(screenshot_path)

    # Using the specialized Computer Use preview model
    response = client.models.generate_content(
        model='gemini-2.5-computer-use-preview', #'gemini-2.0-flash',  # Or 'gemini-2.5-computer-use-preview'
        contents=[goal, img],
        config={'tools': [{'computer_use': {}}]}  # If using native tool
    )
    return response.text  # Parse this for actions like "tap at [500, 200]"
