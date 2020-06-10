from web_driver_dependencies import *
from helium import *

def get_available_episodes(show, vod_base_url, base_url, driver, times_tried=1):

    # Set up helium
    set_driver(driver)
    Config.implicit_wait_secs = 3
    driver.set_window_size(1920, 1080)

    # Seach for existence of 404
    if "Watch Free TV & Movies Online | Stream Full Length Videos | Tubi" in driver.title:
        print("Page no longer found.\n")
        return None

    # Search for the existince of the seasons button, if it exists, use the multiseason function.
    try:
        seasons_available = find_all(S("#parental"))
        if (seasons_available):
            return search_for_multi_season_content(show, vod_base_url, driver)
        else:
            return search_for_single_season_content(show, vod_base_url, driver)

    except TimeoutException:
        # The element doesnt exist or took too long to load.
        try:
            episode_content = driver.find_elements_by_xpath\
                ('//div[starts-with(@class, "Col") and contains(@class, "Col--6") and contains(@class, "Col--lg-4")]')

            if times_tried > 3 or not episode_content:
                print("Episodes no longer found.\n")
                driver.quit()
                return None
            else:
                print("No Videos Found, Trying Once More...")
                driver.quit()
                driver = webdriver.Chrome(chrome_options=chrome_options)
                return get_available_episodes(show, vod_base_url, base_url, driver, times_tried + 1)

        # The element didnt load so the whole page needs to be reloaded.
        except NoSuchElementException:
            print("Loading took too much time, retrying...")
            driver.quit()
            driver = webdriver.Chrome(chrome_options=chrome_options)
            driver.get(vod_base_url+show)
            return get_available_episodes(show, vod_base_url, base_url, driver, times_tried + 1)

    except NoSuchElementException:
        print("No Videos to download in nosuchelement exeption\n")
        driver.quit()
        return None

    except WebDriverException as e:
        print(e)
        driver.quit()
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get(vod_base_url+show)
        return get_available_episodes(show, vod_base_url, base_url, driver, times_tried + 1)

def search_for_multi_season_content(show, vod_base_url, driver):

    #episode_content = WebDriverWait(driver, 5)\
    WebDriverWait(driver, 5)\
        .until(EC.presence_of_element_located((By.XPATH,\
        '//div[starts-with(@class, "Carousel") and contains (@class, "Carousel--no-mask")]')))

    seasons_button = find_all(S("#parental"))[0]

    #Show Seasons
    click(seasons_button)

    # While seasons are shown, get all the available elements.
    seasons_elements = find_all(S("#parental"))[0].web_element\
        .find_element_by_xpath('//ul[starts-with(@class, "Select__list")]')\
        .find_elements_by_xpath('//li[starts-with(@class, "Select__listItem")]')

    seasons_button_text = [ 
        season.get_attribute('innerHTML')
        for season in seasons_elements ]

    episodes = []

    for index, season_text in enumerate(seasons_button_text):

        season_button = find_all(S("#parental"))[0].web_element\
            .find_element_by_xpath('//ul[starts-with(@class, "Select__list")]')\
            .find_element_by_xpath('*[@data-value="' + season_text + '"]')

        click(season_button)

        season = WebDriverWait(driver, 5)\
            .until(EC.presence_of_element_located((By.XPATH,\
            '//div[starts-with(@class, "Carousel") and contains (@class, "Carousel--no-mask")]')))\
            .find_elements_by_xpath\
            ('//div[starts-with(@class, "Col") and contains(@class, "Col--6") and contains(@class, "Col--lg-4")]')

        formatted = search_for_links(season)

        for episode in formatted:
            episodes.append(episode)

        click(seasons_button) # Show Seasons


    return episodes

def search_for_single_season_content(show, vod_base_url, driver):

    season = WebDriverWait(driver, 5)\
        .until(EC.presence_of_element_located((By.XPATH,\
        '//div[starts-with(@class, "Carousel") and contains (@class, "Carousel--no-mask")]')))\
        .find_elements_by_xpath\
        ('//div[starts-with(@class, "Col") and contains(@class, "Col--6") and contains(@class, "Col--lg-4")]')

    return search_for_links(season)


def search_for_links(parsed_html):

    return [ {
        "title" : row.find_element_by_class_name("_1g4Iu").get_attribute('innerText'),
        "url" : row.find_element_by_class_name("_2zACE").get_attribute('href')
        } for row in parsed_html ]
