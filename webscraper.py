from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
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
browser = webdriver.Chrome(options=chrome_options, service_log_path='selenium-logs.txt')
browser.set_page_load_timeout(15)

browser.get('http://www.sunnyportal.com')

# Logging in
user_element = browser.find_element_by_id("txtUserName")
user_element.send_keys(email)
pass_element = browser.find_element_by_id("txtPassword")
pass_element.send_keys(password)
submit = browser.find_element_by_id("ctl00_ContentPlaceHolder1_Logincontrol1_LoginBtn")
submit.click() 


"""
Note:
If this script is run late at night, the daily data won't be available, and the default view will be on the month tab
Thus, we check if the daily data tab is available - if it is, we know we had defaulted to the monthly data tab, and so we can only get monthly data
If it isn't then both daily and monthly data is available, and we try to grab both
"""

try :
    daily_data_tab = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_LinkButton_TabFront3")


except :
    print("Daily data available")

    # Wait for page to load
    wait = WebDriverWait(browser, 10)
    download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_ImageButtonDownload')))

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


    monthly_data_tab = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_LinkButton_TabBack1")

    monthly_data_tab.click()
    time.sleep(8)


finally :
    wait = WebDriverWait(browser, 10)
    download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_ImageButtonDownload')))


    # Getting monthly data 

    # Make sure no extra CSV files have already been downloaded
    download_file_path = download_path + "/Energy_and_Power_Month.csv"
    if os.path.exists(download_file_path):
        os.remove(download_file_path)

    prev_month = 0
    while (True) :

        month_selector = Select(browser.find_element_by_name("ctl00$ContentPlaceHolder1$UserControlShowDashboard1$UserControlShowEnergyAndPower1$DatePickerMonth"))
        month_selected = month_selector.first_selected_option.text.strip()

        year_selector = Select(browser.find_element_by_name("ctl00$ContentPlaceHolder1$UserControlShowDashboard1$UserControlShowEnergyAndPower1$DatePickerYear"))
        year_selected = year_selector.first_selected_option.text.strip()        
        
        if (month_selected == prev_month) :
            print("Month selected: " + month_selected)
            print("Previous month: " + prev_month)

            # browser.save_screenshot("test.png")
            print("Repeated month detected, trying again")

            time.sleep(10)
            month_selector = Select(browser.find_element_by_name("ctl00$ContentPlaceHolder1$UserControlShowDashboard1$UserControlShowEnergyAndPower1$DatePickerMonth"))
            month_selected = month_selector.first_selected_option.text.strip()
            if (month_selected == prev_month) :
                break            


        prev_month = month_selected

        print("Getting data from " + month_selected + " " + year_selected)


        try :
            wait = WebDriverWait(browser, 10)
            download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_ImageButtonDownload')))
        
        # If data cannot be found and the wait times out, immediately go to next page
        except :

            print("Timed out, data could not be found, skipping")

            prev_month_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_btn_prev")
            prev_month_button.click()

            time.sleep(8)
            continue


        # Hover over the menu button to show download button
        menu_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_OpenButtonsDivImg")
        hover = ActionChains(browser).move_to_element(menu_button)
        hover.perform()

        # If file has already been downloaded, remove older version
        download_file_path = download_path + "/Energy_and_Power_Month.csv"
        updated_file_path = download_path + "/Energy_and_Power_" + month_selected + "_" + year_selected + ".csv"
        if os.path.exists(updated_file_path):
            os.remove(updated_file_path)

        # download latest csv
        download.click()

        # Wait until the file has finished downloading
        while not os.path.exists(download_file_path):
            time.sleep(1)

        os.rename(download_file_path, updated_file_path)

        prev_month_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_btn_prev")
        prev_month_button.click()

        time.sleep(4)



    time.sleep(8)

    print("Getting yearly data")

    # Getting yearly data
    # Navigate to yearly tab
    yearly_data_tab = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_LinkButton_TabBack2")
    yearly_data_tab.click();
    time.sleep(4)

    # Make sure no extra CSV files have already been downloaded
    download_file_path = download_path + "/Energy_and_Power_Year.csv"
    if os.path.exists(download_file_path):
        os.remove(download_file_path)

    prev_year = 0
    while (True) :

        year_selector = Select(browser.find_element_by_name("ctl00$ContentPlaceHolder1$UserControlShowDashboard1$UserControlShowEnergyAndPower1$DatePickerYear"))
        year_selected = year_selector.first_selected_option.text.strip()
        
        if (year_selected == prev_year) :

            time.sleep(10)
            year_selector = Select(browser.find_element_by_name("ctl00$ContentPlaceHolder1$UserControlShowDashboard1$UserControlShowEnergyAndPower1$DatePickerYear"))
            year_selected = year_selector.first_selected_option.text.strip()
            if (year_selected == prev_year) :
                break     


        prev_year = year_selected

        try :
            wait = WebDriverWait(browser, 10)
            download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_ImageButtonDownload')))
        
        # If data cannot be found and the wait times out, immediately go to next page
        except :
            prev_year_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_btn_prev")
            prev_year_button.click()

            time.sleep(4)
            continue

        # Hover over the menu button to show download button
        menu_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_OpenButtonsDivImg")
        hover = ActionChains(browser).move_to_element(menu_button)
        hover.perform()

        # If file has already been downloaded, remove older version
        download_file_path = download_path + "/Energy_and_Power_Year.csv"
        updated_file_path = download_path + "/Energy_and_Power_" + year_selected + ".csv"
        if os.path.exists(updated_file_path):
            os.remove(updated_file_path)

        # download latest csv
        download.click()

        # Wait until the file has finished downloading
        while not os.path.exists(download_file_path):
            time.sleep(1)

        os.rename(download_file_path, updated_file_path)

        prev_year_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_btn_prev")
        prev_year_button.click()

        time.sleep(4)


    print("Getting total data")

    # Getting total data
    total_data_tab = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_LinkButton_TabBack3")
    total_data_tab.click();
    time.sleep(8)


    wait = WebDriverWait(browser, 10)
    download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_ImageButtonDownload')))


    # Hover over the menu button to show download button
    menu_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlShowDashboard1_UserControlShowEnergyAndPower1_OpenButtonsDivImg")
    hover = ActionChains(browser).move_to_element(menu_button)
    hover.perform()

    # If file has already been downloaded, remove older version
    now = datetime.datetime.now()
    file_path = download_path + "/Energy_and_Power_Total.csv"
    if os.path.exists(file_path):
        os.remove(file_path)

    # download latest csv
    download.click()

    # Wait until the file has finished downloading
    while not os.path.exists(file_path):
        time.sleep(1)

    print("All data retrieved successfully")

browser.quit()
