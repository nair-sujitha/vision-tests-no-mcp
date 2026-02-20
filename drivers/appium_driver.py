from appium import webdriver
from appium.options.common import AppiumOptions

def get_driver(platform):
    options = AppiumOptions()
    if platform == "android":
        options.load_capabilities({
            "platformName": "Android",
            "automationName": "UiAutomator2",
            "appPackage": "com.homedepot.mcommerce", # Example package
            "appActivity": ".MainActivity"
        })
    else: # iOS
        options.load_capabilities({
            "platformName": "iOS",
            "automationName": "XCUITest",
            "bundleId": "com.homedepot.HomeDepot"
        })
    return webdriver.Remote("http://localhost:4723", options=options)


def get_scaled_coordinates(driver, ai_x, ai_y):
    # Get actual screen size from the device
    size = driver.get_window_size()
    actual_w = size['width']
    actual_h = size['height']

    # Scale the 0-1000 AI coordinate to actual pixels
    scaled_x = int(ai_x * (actual_w / 1000))
    scaled_y = int(ai_y * (actual_h / 1000))

    return scaled_x, scaled_y

def scale_coordinates(gemini_x, gemini_y, screen_w, screen_h):
    actual_x = (gemini_x / 1000) * screen_w
    actual_y = (gemini_y / 1000) * screen_h
    return int(actual_x), int(actual_y)
