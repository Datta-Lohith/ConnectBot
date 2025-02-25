'''
Author:     Datta Lohith Gannavarapu
LinkedIn:   https://www.linkedin.com/in/datta-lohith/

Copyright (C) 2024 Datta Lohith Gannavarapu

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/Datta-Lohith/Connect-Bot
'''


import pyautogui
pyautogui.FAILSAFE = False
from random import choice, shuffle, randint
from modules.open_chrome import *
from yaml import safe_load
from modules.helpers import *
from modules.clickers_and_finders import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchWindowException

config = safe_load(open("setup/config.yaml", "r"))
secrets = safe_load(open("setup/secrets.yaml", "r"))

# Function to check if user is logged-in in LinkedIn
def is_logged_in_LN():
    if driver.current_url == "https://www.linkedin.com/feed/": return True
    if try_linkText(driver, "Sign in"): return False
    if try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]'):  return False
    if try_linkText(driver, "Join now"): return False
    print_lg("Didn't find Sign in link, so assuming user is logged in!")
    return True

# Function to login for LinkedIn
def login_LN():
    # Find the username and password fields and fill them with user credentials
    driver.get("https://www.linkedin.com/login")
    try:
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
        try:
            text_input_by_ID(driver, "username", secrets["username"], 1)
        except Exception as e:
            print_lg("Couldn't find username field.")
            # print_lg(e)
        try:
            text_input_by_ID(driver, "password", secrets["password"], 1)
        except Exception as e:
            print_lg("Couldn't find password field.")
            # print_lg(e)
        # Find the login submit button and click it
        driver.find_element(By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]').click()
    except Exception as e1:
        try:
            profile_button = find_by_class(driver, "profile__details")
            profile_button.click()
        except Exception as e2:
            # print_lg(e1, e2)
            print_lg("Couldn't Login!")

    try:
        # Wait until successful redirect, indicating successful login
        wait.until(EC.url_to_be("https://www.linkedin.com/feed/")) # wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space(.)="Start a post"]')))
        return print_lg("Login successful!")
    except Exception as e:
        print_lg("Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!")
        # print_lg(e)
        manual_login_retry(is_logged_in_LN, 2)


# Function to get pagination element and current page number
def get_page_info():
    try:
        pagination_element = try_xp(driver, ".//div[contains(@class,'artdeco-pagination--has-controls')]", False)
        if not pagination_element:
            pagination_element = try_find_by_classes(driver, ["artdeco-pagination", "artdeco-pagination__pages", "artdeco-pagination__pages--number"])
        scroll_to_view(driver, pagination_element)
        current_page = int(pagination_element.find_element(By.XPATH, "//li[contains(@class, 'active')]").text)
    except Exception as e:
        print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
        pagination_element = None
        current_page = None
    return pagination_element, current_page


# Function to send connection request
def connect_with_person(profile_url, window, person_name, searchTerm):
    try:
        driver.switch_to.window(window)
        driver.get(profile_url)
        sleep(3)
            
        if try_xp(driver, "(//span[@class='artdeco-button__text'][normalize-space()='Pending'])[2]", False):
            return False
        
        # Checks for two types of Connect buttons and clicks on them and returns True if successful
        connect_button = (
            hard_click(actions, try_xp(driver, "(//button[contains(@class, 'artdeco-button--primary') and .//span[text()='Connect']])[2]", False)) or
            hard_click(actions, try_xp(driver, "(//button[contains(@class, 'artdeco-button--secondary') and .//span[text()='Connect']])[2]", False))
        )

        # If Connect button is not found, then tries to click on More actions and then Connect button
        if not connect_button:
            more_actions = try_xp(driver, "//button[@aria-label='More actions']", False)
            if more_actions:
                hard_click(actions, try_xp(driver, "(//button[@aria-label='More actions'])[2]", False))
                sleep(1)
                connect_button = hard_click(actions, try_xp(driver, "(//span[@class='display-flex t-normal flex-1'][normalize-space()='Connect'])[2]",False))

        if not connect_button:
            print_lg("Couldn't find Connect button, so skipping this person!")
            return False
        
    except Exception as e:
        print_lg("Couldn't find Connect button, so skipping this person!")
        return False
        
    if config["add_note"]: add_note_and_send(person_name, searchTerm)
    else: hard_click(actions, try_xp(driver, "//button[@aria-label='Send without a note']", False))
    
    return True

# Function to add note and send connection request
def add_note_and_send(person_name, searchTerm):
    hard_click(actions, try_xp(driver, "//button[@aria-label='Add a note']", False))
    note_key = f"Hi {person_name},\nI hope you’re doing well! I came across your profile and was impressed by your work. I’m currently exploring job opportunities in the same field and would love to connect to learn from your experiences and insights.\nThank you,\n{config['name']}."
    text_input_by_ID(driver, "custom-message", note_key)
    hard_click(actions, try_xp(driver, "//button[@aria-label='Send invitation']", False))

# Main function
def main():
    try:
        alert_title = "Error Occurred. Closing Browser!"

        # Login to LinkedIn
        driver.get("https://www.linkedin.com/login")
        if not is_logged_in_LN(): login_LN()

        linkedIn_tab = driver.current_window_handle


        for searchTerm in config["search_terms"]:
            current_request = 0
            if current_request >= config["max_connections_per_search"]: break

            # Searches for people in general
            driver.get(f'https://www.linkedin.com/search/results/people/?keywords={searchTerm}&network=%5B"S"%2C"O"%5D')
            
            print_lg("\n________________________________________________________________________________________________________________________\n")
            print_lg(f'\n>>>> Now searching for "{searchTerm}" <<<<\n\n')
            buffer(2)

            while current_request < config["max_connections_per_search"]:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(1)
                pagination_element, current_page = get_page_info()
                driver.execute_script("window.scrollTo(0, 0);")

                # Find all people in current page
                people = driver.find_elements(By.XPATH, '//div[@data-view-name="search-entity-result-universal-template"]')  

                driver.switch_to.new_window('window')
                connections_tab = driver.current_window_handle

                
                for person in people:
                    if config["keep_screen_awake"]: pyautogui.press('shiftright')
                    print_lg("\n-@-\n")

                    driver.switch_to.window(linkedIn_tab)
                    # Get name and profile url
                    link_element = person.find_element(By.TAG_NAME, 'a')
                    profile_url = link_element.get_attribute('href')
                    person_name = ""
                    try:
                        title_element = person.find_element(By.XPATH, './/span[@dir="ltr"]//span[@aria-hidden="true"]')
                        person_name = title_element.text.split("\n")[0]
                        if "1st" in title_element.text.lower():
                            print_lg(f'Skipping "{person_name}", Profile URL: {profile_url}. Is already a connection')
                            continue
                    except: 
                        print_lg("Failed to get title element")
                    
                    print_lg(f'Sending connection request to "{person_name}", Profile URL: {profile_url}')

                    if connect_with_person(profile_url, connections_tab, person_name, searchTerm):
                        current_request += 1
                    else:
                        print_lg(f'Skipped, a previous connection request is pending with "{person_name}"')
                    if current_request > config["max_connections_per_search"]: break
                
                driver.switch_to.window(connections_tab)
                driver.close()
                driver.switch_to.window(linkedIn_tab)

                if current_request < config["max_connections_per_search"]:
                    # Switching to next page
                    if pagination_element == None:
                        print_lg("Couldn't find pagination element, probably at the end page of results!")
                        break
                    try:
                        pagination_element.find_element(By.XPATH, f"//button[@aria-label='Page {current_page+1}']").click()
                        print_lg(f"\n>-> Now on Page {current_page+1} \n")
                    except NoSuchElementException:
                        print_lg(f"\n>-> Didn't find Page {current_page+1}. Probably at the end page of results!\n")
                        break


    except NoSuchWindowException:   pass
    except Exception as e:
        critical_error_log("In Connector Main", e)
        pyautogui.alert(e,alert_title)
    finally:
        quote = choice([
            "You're one step closer than before.", 
            "All the best with your future interviews.", 
            "Keep up with the progress. You got this.", 
            "If you're tired, learn to take rest but never give up.",
            "Success is not final, failure is not fatal: It is the courage to continue that counts. - Winston Churchill",
            "Believe in yourself and all that you are. Know that there is something inside you that is greater than any obstacle. - Christian D. Larson",
            "Every job is a self-portrait of the person who does it. Autograph your work with excellence.",
            "The only way to do great work is to love what you do. If you haven't found it yet, keep looking. Don't settle. - Steve Jobs",
            "Opportunities don't happen, you create them. - Chris Grosser",
            "The road to success and the road to failure are almost exactly the same. The difference is perseverance.",
            "Obstacles are those frightful things you see when you take your eyes off your goal. - Henry Ford",
            "The only limit to our realization of tomorrow will be our doubts of today. - Franklin D. Roosevelt"
            ])
        msg = f"\n{quote}\n\n\nBest regards,\nDatta Lohith Gannavarapu\nhttps://www.linkedin.com/in/datta-lohith/\n\n"
        pyautogui.alert(msg, "Exiting..")
        print_lg(msg,"Closing the browser...")
        try: driver.quit()
        except Exception as e: critical_error_log("When quitting...", e)

main()