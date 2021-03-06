import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
from urllib3.exceptions import MaxRetryError

from bs4 import BeautifulSoup

#TEMP
import os;
os.environ["PATH"] += os.pathsep + r'/usr/lib/chromium-browser/';
#########

#DRIVER_LOCATION = '/usr/lib/chromium-browser/chromedriver'

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")  #Temp
chrome_options.add_argument("--start-maximized")
chrome_options.binary_location = '/usr/bin/chromium-browser'
