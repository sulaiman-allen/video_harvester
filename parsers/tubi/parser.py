from web_driver_dependencies import *
from helium import *

def get_parsed_html(show, vod_base_url, driver, times_tried=1):

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
                return get_parsed_html(show, vod_base_url, driver, times_tried + 1)

        # The element didnt load so the whole page needs to be reloaded.
        except NoSuchElementException:
            print("Loading took too much time, retrying...")
            driver.quit()
            driver = webdriver.Chrome(chrome_options=chrome_options)
            driver.get(vod_base_url+show)
            return get_parsed_html(show, vod_base_url, driver, times_tried + 1)

    except NoSuchElementException:
        print("No Videos to download in nosuchelement exeption\n")
        driver.quit()
        return None

    except WebDriverException as e:
        print(e)
        driver.quit()
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get(vod_base_url+show)
        return get_parsed_html(show, vod_base_url, driver, times_tried + 1)

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


    # Get the location for the center point of each season button. Clicking by element xpath doesn't consistantly
    # work so instead, coordinates are used.
    season_button_dimensions = [ {
        "x" : season.location['x'] + (season.size['width'] / 2),
        "y" : season.location['y'] + (season.size['height'] / 2)
        } for season in seasons_elements ]

    episodes = []

    for index, element in enumerate(season_button_dimensions):

        # Click the center of each season's button to load episodes for that specific season.
        click(Point(x=element['x'], y=element['y']))

        season = WebDriverWait(driver, 5)\
            .until(EC.presence_of_element_located((By.XPATH,\
            '//div[starts-with(@class, "Carousel") and contains (@class, "Carousel--no-mask")]')))\
            .find_elements_by_xpath\
            ('//div[starts-with(@class, "Col") and contains(@class, "Col--6") and contains(@class, "Col--lg-4")]')

        formatted = [ {
            "title" : row.find_element_by_class_name("_1g4Iu").get_attribute('innerText'),
            "url" : row.find_element_by_class_name("_2zACE").get_attribute('href')
            } for row in season ]

        for episode in formatted:
            episodes.append(episode)

        click(seasons_button) # Show Seasons

    return episodes

def search_for_single_season_content(show, vod_base_url, driver):

    episode_content = WebDriverWait(driver, 5)\
        .until(EC.presence_of_element_located((By.XPATH,\
        '//div[starts-with(@class, "Carousel") and contains (@class, "Carousel--no-mask")]')))

    season = episode_content.find_elements_by_xpath\
        ('//div[starts-with(@class, "Col") and contains(@class, "Col--6") and contains(@class, "Col--lg-4")]')

    return [ {
        "title" : row.find_element_by_class_name("_1g4Iu").get_attribute('innerText'),
        "url" : row.find_element_by_class_name("_2zACE").get_attribute('href')
        } for row in season ]


def search_for_links(parsed_html, _unused_base_url):

    '''
    return [ {
        "title" : row.find_element_by_class_name("_1g4Iu").get_attribute('innerText'),
        "url" : row.find_element_by_class_name("_2zACE").get_attribute('href')
        } for row in parsed_html ]
    '''
    return parsed_html
