import os
from rq import Queue
from redis import Redis

from shows import shows_dict, vod_base_url, base_url, get_parsed_html, search_for_links
from web_driver_dependencies import *
from general_utils import force_quit_browser_silently, db_connect
from download_helpers import async_logic, check_if_show_is_needed


redis_conn = Redis(host=os.environ["REDIS_HOST"], port=6379)
q = Queue(connection=redis_conn)

def main():

    for show, directory in shows_dict.items():
        # Create webdriver
        #driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
        driver = webdriver.Chrome(options=chrome_options)

        # Open web page
        driver.get(vod_base_url+show)

        # Parse web page and grab html block that has relevant urls
        print("Looking For Episodes of:", shows_dict[show])
        print(vod_base_url+show +"\n") # This maybe needs to go in the parser.
        parsed_html = get_parsed_html(show, vod_base_url, driver)
        if not parsed_html:
            driver.quit()
            continue
        # Search for links
        episodes = search_for_links(parsed_html, base_url)

        # Close webdriver
        driver.quit()

        # Search for existence of show in database. If not found, download.
        for episode in episodes:
            if check_if_show_is_needed(show, episode):
                print("[ ]:", episode['title'])
                # Start download, write nfo and add to database.
                q.enqueue_call(func=async_logic,
                   args=(show, episode),
                   timeout="10m")
            else:
                print("[x]:", episode['title'])

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
