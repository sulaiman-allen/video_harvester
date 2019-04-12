#import re
#import os
#from subprocess import call
#from shows import shows_dict, vod_base_url, base_url
#from download_helpers import get_episode_name_and_path_from_url, download_episode, async_logic
#from nfo_template import nfo_string
from rq import Queue
from redis import Redis

from web_driver_dependencies import *
from shows import shows_dict, vod_base_url
from general_utils import force_quit_browser_silently, db_connect
from download_helpers import async_logic


redis_conn = Redis()
q = Queue(connection=redis_conn)

def search_for_links(parsed_html):
    soup = BeautifulSoup(parsed_html, 'html.parser')
    return [ { # Make sure to update this to remove the ondemand matching
        "url" : element.find('div', {"class": ['c-item__image']}).find('a')["href"],
        "title" : element.find('div', {"class": ['c-item__content']}).find('a').text
     } for element in soup.find_all('div', {"class": ["c-item", "-media"]}) ]
    
def process_episodes(show, episodes, driver):
    con = db_connect()
    cur = con.cursor()

    for episode in episodes:
        cur.execute("SELECT * FROM episodes WHERE show_name = ? AND episode_name = ?",\
            (show, episode['title']))

        if not cur.fetchone():
            print("[ ]:", episode['title'])
            # Start download, write nfo and add to database.
            #print("<<<<<<<<<<< Sending Task To Download Handler.")
            q.enqueue_call(func=async_logic,
                           args=(show, episode),
                           timeout="10m")
            #q.enqueue(async_logic, show, episode)
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

        # Close webdriver
        driver.quit()

        # Search for existence of show in database. If not found, download.
        process_episodes(show, episodes, driver)
        # Close webdriver
        #driver.quit()
        print("\n")

    driver.quit()
    #force_quit_browser_silently()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        print("Main Exception Catcher")
        print(str(e))
        print('Exception caught, type is:', e.__class__.__name__)
        force_quit_browser_silently()
        exit()
