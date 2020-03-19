import os
from web_driver_dependencies import *
from general_utils import force_quit_browser_silently
from shows import shows_dict, base_url
from nfo_template import nfo_string, SELECTED_PARSER

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
        
        WebDriverWait(driver, delay)\
            .until(EC.presence_of_element_located((By.XPATH,\
            "//div[contains(@class, '_3P5Yo')]"))) \

        date_object = driver.find_element(By.XPATH, "//div[contains(@class, '_3P5Yo')]")\
            .get_attribute('innerText')\

        date = date_object.split("\n")[0].split("(")[1].split(")")[0] if "(" in date_object else "Unknown"

        plot = driver.find_element(By.XPATH, "//div[contains(@class, '_1_hc6')]")\
            .get_attribute('innerText')

        nfo_content = {
            "title" : episode['title'].split("- ", 1)[1],
            "date" : date,
            "season" : "Season " + episode['title'].split(":")[0].split("S")[1],
            "episode" : episode['title'].split(":")[1].split("E")[1].split(" ", 1)[0],
            "plot" : plot
        }

        print(nfo_content)

        string_final = nfo_string.substitute(
                title=nfo_content['title'],\
                date=nfo_content['date'],\
                season=nfo_content['season'],\
                episode=nfo_content['episode'],\
                plot=nfo_content['plot']).lstrip()

        directory = shows_dict[show]

        if not os.path.exists("./downloaded/" + SELECTED_PARSER + "/" + directory):
             os.makedirs("./downloaded/" + SELECTED_PARSER + "/" + directory)

        with open("./downloaded/" + SELECTED_PARSER + "/" + path + ".nfo", "w") as nfo:
            nfo.write(string_final)

        driver.quit()

        return nfo_content["date"]

    except TimeoutException:
        print("Fetching nfo took too much time, retrying...")
        print("URL FOR NFO = " + episode['url'])
        return write_nfo(show, episode, path, driver)
    except IndexError:
        print("There was an out of range error because page didn't load correctly, retrying..")
        return write_nfo(show, episode, path, driver)
    except AttributeError as e:
        print("There was an AttributeError here. Retrying")
        print("error = " + e)
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
