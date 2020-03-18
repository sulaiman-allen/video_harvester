from web_driver_dependencies import *

def get_parsed_html(show, vod_base_url, driver, times_tried=1):

    # Seach for existence of 404
    if "Error: 404 Not Found" in driver.title:
        print("Page no longer found.\n")
        return None

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
            contents = driver.find_element_by_xpath('//div[@class="l-contents"]')\
                .find_element_by_class_name('l-contents')\
                .find_element_by_class_name('c-resultHit')\
                .get_attribute('innerText')
            #print("#CONTENTS = ")
            #print(contents)
            if contents == "0 hit":
                print("No Videos currently available for this show.\n")
                driver.quit()
                return None
            if times_tried > 5:
                print("No Videos to download in try block\n")
                driver.quit()
                return None
            else:
                print("No Videos Found, Trying Once More...")
                driver.quit()
                #driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
                driver = webdriver.Chrome(options=chrome_options)
                return get_parsed_html(show, vod_base_url, driver, times_tried + 1)

        # The element didnt load so the whole page needs to be reloaded.
        except NoSuchElementException:
            print("Loading took too much time, retrying...")
            driver.quit()
            #driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(vod_base_url+show)
            return get_parsed_html(show, vod_base_url, driver, times_tried + 1)

    except NoSuchElementException:
        print("No Videos to download in nosuchelement exeption\n")
        driver.quit()
        return None

    except WebDriverException as e:
        print(e)
        driver.quit()
        #driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=chrome_options)
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(vod_base_url+show)
        return get_parsed_html(show, vod_base_url, driver, times_tried + 1)


def search_for_links(parsed_html, base_url):
    soup = BeautifulSoup(parsed_html, 'html.parser')
    return [ {
        "url" : base_url + element.find('div', {"class": ['c-item__image']}).find('a')["href"],
        "title" : element.find('div', {"class": ['c-item__content']}).find('a').text
     } for element in soup.find_all('div', {"class": ["c-item", "-media"]}) ]

