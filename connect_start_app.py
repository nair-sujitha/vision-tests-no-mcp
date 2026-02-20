from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.ui import WebDriverWait
import time

options = UiAutomator2Options()

options.platform_name = "Android"
options.device_name = "emulator-5554"
options.automation_name = "UiAutomator2"

options.app_package = "com.thehomedepotca"
options.app_activity = "com.thehomedepotca.view.splash.activity.SplashActivity"

options.no_reset = True
options.auto_grant_permissions = True

# IMPORTANT: use keyword argument
driver = webdriver.Remote(
    command_executor="http://127.0.0.1:4723",
    options=options
)

time.sleep(5)

driver.terminate_app("com.thehomedepotca")
time.sleep(2)

driver.activate_app("com.thehomedepotca")

WebDriverWait(driver, 20).until(
    lambda d: d.current_package == "com.thehomedepotca"
)

print("Connected to package:", driver.current_package)