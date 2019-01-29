from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup
from subprocess import call, check_output, Popen, PIPE
from subprocess import CalledProcessError
from string import Template

from shows import shows_dict, vod_base_url, base_url

import re
import time
import sys
import sqlite3  
import os


DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'episode_db.sqlite3')

#run pip3 install requests beautifulsoup4
#apt install ffmpeg
#sudo pip install -U youtube-dl

options = Options()
options.headless = True


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

def get_episode_name_and_path_from_url(show, url):

    try:
        #result = check_output([ "youtube-dl", "--get-title", url]).strip().decode('utf-8')
        p = Popen([ "youtube-dl", "--get-title", url], stdout=PIPE, stderr=PIPE)
        result, error = p.communicate()
        error = error.decode('utf-8')
        result = result.decode('utf-8')
        #print(result)
        if p.returncode != 0:
            print("Something else bad happened!")
            print(error) 
            time.sleep(2)
            return get_episode_name_and_path_from_url(show, url)   

        filename = re.sub('[^0-9a-zA-Z\-\_\.\']+', " ", re.sub('[:]+', "-", result))
        filename = filename.strip()
        #directory = titlecase(filename.split("-")[0].strip())
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
    driver.get(url)
    delay = 10 # seconds

    try:
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

        nfo_string = Template(\
        '''
<episodedetails>
  <title>$title</title>
  <season>Unknown</season>
  <aired>$date</aired>
  <plot>$plot</plot>
</episodedetails>
        ''' 
        )
        string_final = nfo_string.substitute(title=nfo_content['title'], \
                date=nfo_content['broadcast_date'], \
                plot=nfo_content['plot']).lstrip()

        path = get_episode_name_and_path_from_url(show, url.replace("ondemand", "vod"))
        #directory = path.split("/")[0].strip()
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
    except NoSuchElementException:
        return print("Something went wrong here Sule!")
    except AttributeError:
        print("There was an AttributeError here. Retrying")
        return write_nfo(episode, show, driver)
    

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
        #"date" : element.find_all('p')[1].text
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
        #print(episode['title'])
        cur.execute("SELECT * FROM episodes WHERE show_name = ? AND episode_name = ?",\
            (show, episode['title']))

        if not cur.fetchone():
            print("[ ]:", episode['title'])
            # Add entry to database
            verify_downloaded = download_episode(show, episode)
            if not verify_downloaded:
               continue 
            air_date = write_nfo(episode, show, driver) 
            episode['date'] = air_date
            add_entry_to_db(show, episode)
        else:
            print("[x]:", episode['title'])

def get_parsed_html(show, driver, times_tried=1):

    print("Looking For Episodes of:", shows_dict[show])
    print(vod_base_url+show +"\n")
    #delay = 12 # seconds
    delay = 5 # seconds
    try:
        return WebDriverWait(driver, delay)\
            .until(EC.presence_of_element_located((By.CLASS_NAME, 'c-itemList')))\
            .get_attribute('outerHTML')
        '''    
        This needs to be updated to scroll to the bottom of the screen and wait rather than clicking a load more button
        try:
            time.sleep(15)
            button = driver.find_element_by_css_selector('.l-container')\
                .find_element_by_css_selector('.c-viewMore__btn')
            driver.execute_script("arguments[0].click();", button)
            time.sleep(5)
            print("More videos found on page\n")
        except NoSuchElementException:
            print("This page doesn't have a button to click for loading more episodes\n")

        return driver.find_element_by_xpath('//div[@class="c-hero"]/\
            following-sibling::div[contains(@class, "l-block")]\
            //child::div[contains(@class, "c-tiles")]')\
            .get_attribute('outerHTML')
        '''    

    except TimeoutException:
        # The element exists, but the content within it doesn't so the page loaded but there are no vids.
        try:
            driver.find_element_by_xpath('//div[@class="l-contents"]')
            if times_tried > 1:
                print("No Videos to download in try block\n")
                driver.quit()
                return None
            else:
                print("No Videos Found, Trying Once More...\n")
                driver.quit()
                driver = webdriver.Firefox(options=options)
                driver.get(vod_base_url+show)
                return get_parsed_html(show, driver, times_tried + 1)

        # The element didnt load so the whole page needs to be reloaded.
        except NoSuchElementException:
            print("Loading took too much time, retrying...")
            driver.quit()
            driver = webdriver.Firefox(options=options)
            driver.get(vod_base_url+show)
            return get_parsed_html(show, driver)

    except NoSuchElementException:
        print("No Videos to download in nosuchelement exeption\n")
        driver.quit()
        return None

def main():

    for show, directory in shows_dict.items():
        # Create webdriver
        driver = webdriver.Firefox(options=options)

        # Open web page
        driver.get(vod_base_url+show)

        # Parse web page and grab html block that has relevant urls
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

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
        call(["ps", "aux", "|", "grep", "firefox", "|", "grep", "-v", "grep", "|", "kill", "$(awk", "'{print $2}')"])
    #except Exception as e:
        #print(str(e))
        #call(["ps", "aux", "|", "grep", "firefox", "|", "grep", "-v", "grep", "|", "kill", "$(awk", "'{print $2}')"])
