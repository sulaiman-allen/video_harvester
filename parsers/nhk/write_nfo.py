import os
from shows import shows_dict
from nfo_template import nfo_string, SELECTED_PARSER
from web_driver_dependencies import *
from general_utils import force_quit_browser_silently

def write_nfo(show, episode, path, driver=None):
    '''
        Returns the date the show aired.
    '''
    # Create driver if the function executed for the first time and was not called recursively.
    if driver == None:
        #driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
        driver = webdriver.Chrome(options=chrome_options)
    delay = 10 # seconds

    try:
        driver.get(episode['url'])
        parsed_html = WebDriverWait(driver, delay)\
            .until(EC.presence_of_element_located((By.XPATH,\
            "//div[contains(@class, 'l-block') and contains(@class, '-lg')]"))) \
            .get_attribute('outerHTML')

        soup = BeautifulSoup(parsed_html, 'html.parser')
        nfo_content = {
            "title" : episode['title'],
            "broadcast_date" : soup.find("span", {"class": ["c-episodeInfo__broadcastDate"]})\
                .find("b").text,
                "plot" : soup.find("div", {"class": ["p-episodeItem__description"]})\
                .find("p").text
        }

        string_final = nfo_string.substitute(title=nfo_content['title'],\
                date=nfo_content['broadcast_date'],\
                plot=nfo_content['plot']).lstrip()

        directory = shows_dict[show]

        if not os.path.exists("./downloaded/" + SELECTED_PARSER + "/" + directory):
            os.makedirs("./downloaded/" + SELECTED_PARSER + "/" + directory)

        with open("./downloaded/" + SELECTED_PARSER + "/" + path + ".nfo", "w") as nfo:
            nfo.write(string_final)

        driver.quit()

        return nfo_content["broadcast_date"]

    except TimeoutException:
        print("Fetching nfo took too much time, retrying...")
        return write_nfo(show, episode, path, driver)
    except IndexError:
        print("There was an out of range error because page didn't load correctly, retrying..")
        return write_nfo(show, episode, path, driver)
    except AttributeError:
        print("There was an AttributeError here. Retrying")
        return write_nfo(show, episode, path, driver)
    except MaxRetryError as e:
        print('Exception caught, type is:', e.__class__.__name__)
        driver.quit()
        time.sleep(5)
        #force_quit_browser_silently()
        #driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
        driver = webdriver.Chrome(options=chrome_options)
        time.sleep(3)
        write_nfo(show, episode, path, driver)
    except Exception as e:
        print(e)
        print('Exception caught, type is:', e.__class__.__name__)
        driver.quit()
        time.sleep(5)
        #force_quit_browser_silently()
        #driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
        driver = webdriver.Chrome(options=chrome_options)
        time.sleep(3)
        write_nfo(show, episode, path, driver)
