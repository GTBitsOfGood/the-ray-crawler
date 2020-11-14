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
browser = webdriver.Chrome(options=chrome_options, service_log_path='selenium-logs-co2.txt')
browser.set_page_load_timeout(15)



# To login, we need to send a post request to SunnyPortal's authentication URL and store the received cookies for the Selenium browser
import requests

# Start the session
session = requests.Session()


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
}

data = {
  '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$Logincontrol1$LoginBtn',
  'ctl00$ContentPlaceHolder1$Logincontrol1$txtUserName': email,
  'ctl00$ContentPlaceHolder1$Logincontrol1$txtPassword': password,
}

response = session.post('https://www.sunnyportal.com/Templates/Start.aspx', headers=headers, data=data) 


# To add the cookies to the domain, must first visit domain then refresh
browser.get('https://www.sunnyportal.com')
for cookie in session.cookies :
    browser.add_cookie({
        'name': cookie.name,
        'domain': cookie.domain,
        'value': cookie.value,
    })

time.sleep(1)
browser.get('https://www.sunnyportal.com')

"""
Note:
If this script is run late at night, the daily data won't be available, and the default view will be on the month tab
Thus, we check if the daily data tab is available - if it is, we know we had defaulted to the monthly data tab, and so we can only get monthly data
If it isn't then both daily and monthly data is available, and we try to grab both
"""

if not os.path.exists('co2') :
    os.mkdir('co2')
if os.path.exists('co2/RETRIEVED_MONTHS.txt'):
    os.remove('co2/RETRIEVED_MONTHS.txt')
if os.path.exists('co2/RETRIEVED_OVERALL_MONTHS.txt'):
    os.remove('co2/RETRIEVED_OVERALL_MONTHS.txt')
if os.path.exists('co2/RETRIEVED_YEARS.txt'):
    os.remove('co2/RETRIEVED_YEARS.txt')
months_retrieved_file = open('co2/RETRIEVED_MONTHS.txt', 'x')
months_overall_retrieved_file = open('co2/RETRIEVED_OVERALL_MONTHS.txt', 'x')
years_retrieved_file = open('co2/RETRIEVED_YEARS.txt', 'x')

co2_navigation_tab = browser.find_element_by_id('TitleLeftMenuNode_1')
co2_navigation_tab.click()

co2_report_tab = browser.find_element_by_id('lmiGroupedPage_94df2906-5b8d-4905-90d5-ba8fa89a7c6f')
co2_report_tab.click()

co2_tab = browser.find_element_by_id('ctl00_NavigationLeftMenuControl_1_0_3')
co2_tab.click()


prev_month = -1
double_time_out = False
wait = WebDriverWait(browser, 10)
download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl1_ImageButtonDownload')))

while True :
     
    date_picker = browser.find_element_by_name("ctl00$ContentPlaceHolder1$UserControlConfigAssistant1$ctl00$UserControl1$_datePicker_start$textBox")
    date = date_picker.get_attribute('value').split('/')
    month = date[0]
    year = date[2]

    if (month == prev_month) :
        print("Month selected: " + month)
        print("Previous month: " + prev_month)

        # browser.save_screenshot("test.png")
        print("Repeated month detected, trying again")

        time.sleep(10)
        date_picker = browser.find_element_by_name("ctl00$ContentPlaceHolder1$UserControlConfigAssistant1$ctl00$UserControl1$_datePicker_start$textBox")
        date = date_picker.get_attribute('value').split('/')
        month = date[0]
        year = date[2]
        if (month == prev_month) :
            break


    prev_month = month
    print("Getting data from " + month + "-" + year)
         

    try :
        wait = WebDriverWait(browser, 10)
        download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl1_ImageButtonDownload')))
    

    # If data cannot be found and the wait times out, immediately go to next page
    except :

        if double_time_out :
            print("Timed out twice, stopping")
            break

        print("Timed out, data could not be found, skipping")
        double_time_out = True

        prev_month_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl1_btn_prev")
        prev_month_button.click()

        time.sleep(6)
        continue


    # Hover over the menu button to show download button
    menu_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl1_OpenButtonsDivImg")
    hover = ActionChains(browser).move_to_element(menu_button)
    hover.perform()


    file_path = download_path + "/Monthly_report_CO2_Diagram_2" + ".csv"
    if os.path.exists(file_path):
        os.remove(file_path)


    download.click()
    time.sleep(3)

    download_failed = False

    wait_count = 0
    # Wait until the file has finished downloading
    while not os.path.exists(file_path):
        time.sleep(1)
        wait_count += 1
        if (wait_count > 45) :
            print("Download failed! Continuing...")
            download_failed = True
            break
    
    
    if not download_failed :
        os.rename(file_path, download_path + '/co2' + "/CO2_" + month + "_" + year + ".csv")
        months_retrieved_file.write(month + '-' + year + '\n')

    prev_month_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl1_btn_prev")
    prev_month_button.click()

    time.sleep(4)



prev_month = -1
wait = WebDriverWait(browser, 10)
download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl0_ImageButtonDownload')))

while True :

    date_picker = browser.find_element_by_id('ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl0_BasicDatePicker1_textBox')
    date = date_picker.get_attribute('value').split('/')
    month = date[0]
    year = date[2]

    if (month == prev_month) :
        print("Month selected: " + month)
        print("Previous month: " + prev_month)

        # browser.save_screenshot("test.png")
        print("Repeated month detected, trying again")

        time.sleep(10)
        date_picker = browser.find_element_by_name("ctl00$ContentPlaceHolder1$UserControlConfigAssistant1$ctl00$UserControl1$_datePicker_start$textBox")
        date = date_picker.get_attribute('value').split('/')
        month = date[0]
        year = date[2]
        if (month == prev_month) :
            break


    prev_month = month
    print("Getting monthly data from " + month + "-" + year)
         

    try :
        wait = WebDriverWait(browser, 10)
        download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl0_ImageButtonDownload')))
    
    # If data cannot be found and the wait times out, immediately go to next page
    except :

        print("Timed out, data could not be found, skipping")

        prev_month_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl0_LinkButtonLastMonth")
        prev_month_button.click()

        time.sleep(6)
        continue


    file_path = download_path + "/Monthly_report_CO2_Table_1" + ".csv"
    if os.path.exists(file_path):
        os.remove(file_path)


    download.click()
    time.sleep(3)

    download_failed = False

    wait_count = 0
    # Wait until the file has finished downloading
    while not os.path.exists(file_path):
        time.sleep(1)
        wait_count += 1
        if (wait_count > 45) :
            print("Download failed! Continuing...")
            download_failed = True
            break
    
    
    if not download_failed :
        os.rename(file_path, download_path + '/co2' + "/CO2_Overall_" + month + "_" + year + ".csv")
        months_overall_retrieved_file.write(month + '-' + year + '\n')

    prev_month_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl0_LinkButtonLastMonth")
    prev_month_button.click()

    time.sleep(4)


    # Hardcoded - should be fine, since The Ray had never gotten data before this point
    if month == "8" and year == "2015" :
        break
    


browser.get('https://www.sunnyportal.com/Templates/DefaultPage.aspx')

prev_year = -1
wait = WebDriverWait(browser, 10)
download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl0_ImageButtonDownload')))

while True :

    date_picker = browser.find_element_by_id('ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl0_BasicDatePicker1_textBox')
    date = date_picker.get_attribute('value').split('/')
    month = date[0]
    year = date[2]

    if (year == prev_year) :
        print("Year selected: " + year)
        print("Previous month: " + prev_year)

        # browser.save_screenshot("test.png")
        print("Repeated month detected, trying again")

        time.sleep(10)
        date_picker = browser.find_element_by_name("ctl00$ContentPlaceHolder1$UserControlConfigAssistant1$ctl00$UserControl1$_datePicker_start$textBox")
        date = date_picker.get_attribute('value').split('/')
        month = date[0]
        year = date[2]
        if (year == prev_year) :
            break
         

    prev_year = year
    print("Getting year data from " + year)


    try :
        wait = WebDriverWait(browser, 10)
        download = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl0_ImageButtonDownload')))
    
    # If data cannot be found and the wait times out, immediately go to next page
    except :

        print("Timed out, data could not be found, skipping")

        prev_year_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl0_LinkbuttonLastYear")
        prev_year_button.click()

        time.sleep(6)
        continue


    file_path = download_path + "/Monthly_report_CO2_Table_1" + ".csv"
    if os.path.exists(file_path):
        os.remove(file_path)


    download.click()
    time.sleep(3)

    download_failed = False

    wait_count = 0
    # Wait until the file has finished downloading
    while not os.path.exists(file_path):
        time.sleep(1)
        wait_count += 1
        if (wait_count > 45) :
            print("Download failed! Continuing...")
            download_failed = True
            break
    
    
    if not download_failed :
        os.rename(file_path, download_path + '/co2' + "/CO2_Overall_" + year + ".csv")
        years_retrieved_file.write(year + '\n')

    prev_year_button = browser.find_element_by_id("ctl00_ContentPlaceHolder1_UserControlConfigAssistant1_ctl00_UserControl0_LinkbuttonLastYear")
    prev_year_button.click()

    time.sleep(4)

    # Hardcoded - should be fine, since The Ray had never gotten data before this point
    if year == "2015" :
        break



months_retrieved_file.close()
months_overall_retrieved_file.close()
years_retrieved_file.close()
browser.quit()
