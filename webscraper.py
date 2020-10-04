from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv
from pathlib import Path  # Python 3.6+ only
import os
import csv
import time
import datetime

# Load login.env
load_dotenv()

# Get username and password for sunnyportal.com
email = os.getenv("username")
password = os.getenv("password")
download_path = str(Path('.').resolve())

print("Email retrieved: " + email)

# Set the download path
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--user-agent="Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; Microsoft; Lumia 640 XL LTE) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Mobile Safari/537.36 Edge/12.10166"')



prefs = {'download.default_directory' : download_path}
chrome_options.add_experimental_option('prefs', prefs)

# Start up the browser and navigate to sunnyportal
browser = webdriver.Chrome(options=chrome_options)
browser.get('http://www.sunnyportal.com')


print("Attempting to login")

# Logging in
user_element = browser.find_element_by_id("txtUserName")
user_element.send_keys(email)
pass_element = browser.find_element_by_id("txtPassword")
pass_element.send_keys(password)
submit = browser.find_element_by_id("ctl00_ContentPlaceHolder1_Logincontrol1_LoginBtn")
submit.click()

print("Logging in")

# Wait for page to load
wait = WebDriverWait(browser, 10)
download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_ImageButtonDownload')))

print("Logged in")

# Hover over the menu button to show download button
menu_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_OpenButtonsDivImg")
hover = ActionChains(browser).move_to_element(menu_button)
hover.perform()

# If file has already been downloaded, remove older version
now = datetime.datetime.now()
file_path = download_path + "/Energy_and_Power_Day_" + str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2) + ".csv"
if os.path.exists(file_path):
    os.remove(file_path)

# download latest csv
download.click()

# Wait until the file has finished downloading
while not os.path.exists(file_path):
    time.sleep(1)

browser.quit()
