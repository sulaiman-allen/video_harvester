from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from urllib3.exceptions import MaxRetryError

from bs4 import BeautifulSoup
from subprocess import call, check_output, Popen, PIPE
from subprocess import CalledProcessError
from string import Template

import re
import time
import sys
import sqlite3  
import os
import requests

from shows import shows_dict, vod_base_url, base_url
from nfo_template import nfo_string

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'episode_db.sqlite3')
DRIVER_LOCATION = '/usr/lib/chromium-browser/chromedriver'

chrome_options = Options()  
chrome_options.add_argument("--headless")  
chrome_options.add_argument("--no-sandbox")  #Temp
chrome_options.binary_location = '/usr/bin/chromium-browser'  


def db_connect(db_path=DEFAULT_PATH):
    return sqlite3.connect(db_path)  

def titlecase(s):
    '''
        Used for folder naming. I didn't write this.
    '''
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
        lambda mo: mo.group(0)[0].upper() +
            mo.group(0)[1:].lower(),
        s)

def force_quit_browser_silently():
    FNULL = open(os.devnull, 'w')

    call([
        "ps", "aux", "|",
        "grep", "chromium", "|",
        "grep", "-v", "grep", "|",
        "kill", "$(awk", "'{print $2}'", "&>", "/dev/null"
    ], shell=True, stdout=FNULL)

    #kill $(ps -A -ostat,ppid | awk '/[zZ]/ && !a[$2]++ {print $2}')

    print("Force Quitting Browser...")

def get_episode_name_and_path_from_url(show, url):

    try:
        p = Popen([ "youtube-dl", "--get-title", url], stdout=PIPE, stderr=PIPE)
        result, error = p.communicate()
        error = error.decode('utf-8')
        result = result.decode('utf-8')
        if p.returncode != 0:
            print(error)
            time.sleep(2)
            return get_episode_name_and_path_from_url(show, url)   

        filename = re.sub('[^0-9a-zA-Z\-\_\.\']+', " ", re.sub('[:]+', "-", result))
        filename = filename.strip()
        directory = shows_dict[show].strip()
        return directory + '/' + filename

    except CalledProcessError as error:
        print("Getting the episode name threw an error. Retrying...")
        #print("resp = ", error.output.decode('utf8'))
        time.sleep(2)
        return get_episode_name_and_path_from_url(show, url)   


def write_nfo(episode, show, driver):
    '''
        Returns the date the show aired.
    '''
    url = base_url + episode['url']
    delay = 10 # seconds

    try:
        driver.get(url)
        parsed_html = WebDriverWait(driver, delay)\
            .until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'l-block') and contains(@class, '-lg')]"))) \
            .get_attribute('outerHTML')

        soup = BeautifulSoup(parsed_html, 'html.parser')
        nfo_content = {
            "title" : episode['title'],
            "broadcast_date" : soup.find("span", {"class": ["c-episodeInfo__broadcastDate"]})\
                    .find("b").text,
                    "plot" : soup.find("div", {"class": ["p-episodeItem__description"]})\
                    .find("p").text
        }

        string_final = nfo_string.substitute(title=nfo_content['title'], \
                date=nfo_content['broadcast_date'], \
                plot=nfo_content['plot']).lstrip()

        path = get_episode_name_and_path_from_url(show, url.replace("ondemand", "vod"))
        directory = shows_dict[show]

        if not os.path.exists("./downloaded/" + directory):
             os.makedirs("./downloaded/" + directory)

        with open("./downloaded/" + path + ".nfo", "w") as nfo:
            nfo.write(string_final)

        return nfo_content["broadcast_date"]

    except TimeoutException:
        print("Fetching nfo took too much time, retrying...")
        return write_nfo(episode, show, driver)
    except IndexError:
        print("There was an out of range error because page didn't load correctly, retrying..")
        return write_nfo(episode, show, driver)
    except AttributeError:
        print("There was an AttributeError here. Retrying")
        return write_nfo(episode, show, driver)
    except MaxRetryError as e:
        print('Exception caught, type is:', e.__class__.__name__)
        driver.quit()
        time.sleep(5)
        force_quit_browser_silently()
        driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
        time.sleep(3)
        write_nfo(episode, show, driver)
    except Exception as e:
        print(e)
        print('Exception caught, type is:', e.__class__.__name__)
        driver.quit()
        time.sleep(5)
        force_quit_browser_silently()
        driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
        time.sleep(3)
        write_nfo(episode, show, driver)
    

def download_episode(show, episode):
    '''
        Returns true if episode downloaded correctly, false otherwise
    '''

    url = base_url + episode['url'].replace("ondemand", "vod")

    try:
        path = get_episode_name_and_path_from_url(show, url)

        if not path:
            return None

        p = Popen([\
            "youtube-dl", \
            "--write-thumbnail", \
            "--external-downloader", "axel", \
            "--external-downloader-args", "'-n 15 -a -k'", \
            "--format", "best", \
            "-o", './downloaded/' + path + '.%(ext)s', url \
        ], stderr=PIPE)

        error = p.communicate()

        if p.returncode != 0: 
            error =  error[1].decode("utf-8")
            if "ERROR: Unable to find episode" in error:
                print("###########Epsisode couldn't be downloaded")
                return False

            print("There was an error, pausing for a moment before contiuing...")
            time.sleep(2)
            print("Redownloading ", episode['title'])
            return download_episode(show, episode)

        return True

    except CalledProcessError:
        print("\n!!!!!Error Happened Here !!!!!!!\n")
        print("Redownloading ", episode['title'])
        time.sleep(2)
        return download_episode(show, episode)

def search_for_links(parsed_html):
    soup = BeautifulSoup(parsed_html, 'html.parser')
    return [ { # Make sure to update this to remove the ondemand matching
        "url" : element.find('div', {"class": ['c-item__image']}).find('a')["href"],
        "title" : element.find('div', {"class": ['c-item__content']}).find('a').text
     } for element in soup.find_all('div', {"class": ["c-item", "-media"]}) ]

def add_entry_to_db(show, episode):
    con = db_connect()
    cur = con.cursor()
    show_sql = "INSERT INTO episodes (show_name, url, episode_name, date) VALUES (?, ?, ?, ?)"
    cur.execute(show_sql, (show, episode['url'], episode['title'], episode['date']))
    con.commit()
    
def process_episodes(show, episodes, driver):
    con = db_connect()
    cur = con.cursor()

    for episode in episodes:
        cur.execute("SELECT * FROM episodes WHERE show_name = ? AND episode_name = ?",\
            (show, episode['title']))

        if not cur.fetchone():
            print("[ ]:", episode['title'])

            # Add entry to database
            #print("<<<<<<<<<<<")
            verify_downloaded = download_episode(show, episode)
            if not verify_downloaded:
               continue 

            air_date = write_nfo(episode, show, driver) 
            episode['date'] = air_date
            add_entry_to_db(show, episode)
        else:
            print("[x]:", episode['title'])

def get_parsed_html(show, driver, times_tried=1):

    delay = 5 # seconds
    try:
        WebDriverWait(driver, delay)\
            .until(EC.presence_of_element_located((By.CLASS_NAME, 'c-itemList')))\

        SCROLL_PAUSE_TIME = 1

        # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")
        distance_counter = 0
        scroll_distance = [.40, .50, .63, .70, .74, .79]
        while True:
            scroll_max = driver.execute_script("return document.body.scrollHeight")
            multiplier = scroll_distance[distance_counter]
            result = float(scroll_max) * float(multiplier)
            driver.execute_script("window.scrollTo(0, parseInt(" + str(result) + "));")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
            	break
            last_height = new_height
            distance_counter = distance_counter + 1 if distance_counter + 1 != len(scroll_distance) else distance_counter

        return WebDriverWait(driver, delay)\
            .until(EC.presence_of_element_located((By.CLASS_NAME, 'c-itemList')))\
            .get_attribute('outerHTML')

    except TimeoutException:
        # The element exists, but the content within it doesn't so the page loaded but there are no vids.
        try:
            driver.find_element_by_xpath('//div[@class="l-contents"]')
            if times_tried > 5:
                print("No Videos to download in try block\n")
                driver.quit()
                return None
            else:
                print("No Videos Found, Trying Once More...")
                driver.quit()
                driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
                return get_parsed_html(show, driver, times_tried + 1)

        # The element didnt load so the whole page needs to be reloaded.
        except NoSuchElementException:
            print("Loading took too much time, retrying...")
            driver.quit()
            driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
            driver.get(vod_base_url+show)
            return get_parsed_html(show, driver, times_tried + 1)

    except NoSuchElementException:
        print("No Videos to download in nosuchelement exeption\n")
        driver.quit()
        return None

    except WebDriverException as e:
        print(e)
        driver.quit()
        driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
        driver.get(vod_base_url+show)
        return get_parsed_html(show, driver, times_tried + 1)


def main():

    for show, directory in shows_dict.items():
        # Create webdriver
        driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)

        # Open web page
        driver.get(vod_base_url+show)

        # Parse web page and grab html block that has relevant urls
        print("Looking For Episodes of:", shows_dict[show])
        print(vod_base_url+show +"\n")
        parsed_html = get_parsed_html(show, driver)
        if not parsed_html:
            driver.quit()
            continue
        # Search for links
        episodes = search_for_links(parsed_html)
        # Search for existence of show in database. If not found, download.
        process_episodes(show, episodes, driver)
        # Close webdriver
        driver.quit()
        print("\n")

    driver.quit()
    force_quit_browser_silently()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        print("Main Exception Catcher")
        print(str(e))
        print('Exception caught, type is:', e.__class__.__name__)
        force_quit_browser_silently()
        sys.exit()
