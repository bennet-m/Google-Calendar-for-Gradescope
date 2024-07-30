import shutil
from webbrowser import Error
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta
from uI import *
from scheduling import *
import pickle
import os
import tempfile
import sys
from pathlib import Path
from macPath import *
#import chromedriver_autoinstaller
import warnings
import urllib3
import certifi
import urllib.request
import ssl
from webdriverSetup import get_driver

#logger
import logging
logger = logging.getLogger(__name__)

def scraping():
    """
    Scrapes Gradescope for assignments and returns them as a list of events.

    Returns:
        (arr): An array of event dictionaries formated for the google calendar api
    """
        
    ##DEFINE FUNCTIONS##
 
    
    def purdue_login(client_username, client_password):
        print("going to Purdue login page")
        driver.get("https://www.gradescope.com/login")
        # Find the username and password fields once page loads sufficiently
        username = WebDriverWait(driver, 500).until(
            EC.element_to_be_clickable((By.ID, "session_email"))  
        )
        password = driver.find_element(By.ID, "session_password")
        print("logging in", client_username, client_password)
        username.send_keys(client_username)
        password.send_keys(client_password)
        password.send_keys(Keys.RETURN)
            
    def mudd_login(client_username, client_password):
        print("going to mudd_login page")
        driver.get("https://www.gradescope.com/auth/saml/hmc")
        # Find the username and password fields once page loads sufficiently
        username = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "identification"))  
        )
        password = driver.find_element(By.ID, "ember533") 

        # Submit credentials
        username.send_keys(client_username)
        password.send_keys(client_password)
        password.send_keys(Keys.RETURN)
    
    def login():
        while True:
            school, client_username, client_password = get_login()
            if school == "Harvey Mudd College":
                mudd_login(client_username, client_password)
                try:
                    print("testing to see if Mudd password is right")
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "cs-error"))  
                    )
                    #Notify user of incorrect information
                    incorrect_login()
                    print("Incorrect User Info")
                    
                except:
                    print("trying duo")
                    #notify user of duo push
                    duo() 
                    print("looking for trust")
                    trust = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "trust-browser-button"))  
                    )
                    print("ok found it")
                    
                    trust.click()
                    print("Correct User Loggin")
                    break
                    
            else:
                purdue_login(client_username, client_password)
                try:
                    print("testing to see if password is right")
                    driver.find_element(By.CLASS_NAME, "courseList--term")
                    
                    print("Correct User Loggin")
                    break
                except:
                    #Notify user of incorrect information
                    incorrect_login()
                    print("Incorrect User Info")

    def assignmentElementToEvent(assignment, course, default_href):
        '''
        Converts an assignment element to an event dictionary.

        Args:
            assignment: The assignment html element 
            course:     Name of the course we're searching in

        Returns:
            event: A dictionary with all the relevent data from the assignment and formating data for the google calendar api
                (course name, assignment name, assignment link, due date)
        '''
        #get the assignment name and href
        assignment_primary = assignment.find_element(By.CLASS_NAME, "table--primaryLink")
        assignment_name = assignment_primary.text
        try:
            assignment_href = assignment_primary.find_element(By.TAG_NAME, "a").get_attribute("href")
        except:
            assignment_href = default_href
        #get the assignmentDue Date
        try:
            due_date_element = assignment.find_element(By.CLASS_NAME, "submissionTimeChart--dueDate")
        except:
            print("there's no due date for assignment {assignment}")
            return
        due_date_unformatted = due_date_element.get_attribute("datetime")

        # Change Due Date format to Google Calendar's format
        obj = datetime.strptime(due_date_unformatted, '%Y-%m-%d %H:%M:%S %z')
        due_date = obj.strftime("%Y-%m-%d") + "T" + obj.strftime("%H:%M:%S") + obj.strftime("%z")[0:3] + ':' + obj.strftime("%z")[3:5]

        # Create a start date 30 minutes before the assignment is due
        start_date_obj = obj - timedelta(minutes=30)
        start_date = start_date_obj.strftime("%Y-%m-%d") + "T" + start_date_obj.strftime("%H:%M:%S") + start_date_obj.strftime("%z")[0:3] + ':' + start_date_obj.strftime("%z")[3:5]

        event = {
            'summary': assignment_name,
            'description': course + "\n" + assignment_href,
            'colorId': "7",
            'start': {
                'dateTime': start_date,
            },
            'end': {
                'dateTime': due_date,
            },
            'reminders': {
                'useDefault': True,
            },
        }
        print("event is", event)
        return event
    
    def has_no_submission(assignment):
        return "No Submission" in assignment.text

    def assignment_scrape(href):
        '''
        Scrapes a Gradescope course page for assignments for the current user date
        and organizes the data into an array of event dictionaries.

        Args:
            href (str): Gradescope course href string as an input

        Returns:
            (arr): An array of event dictionaries formated for the google calendar api
        '''

        if href == "https://www.gradescope.com":
            return []
        #get the course page
        driver.get(href)

        #wait for it to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "courseHeader--title"))
        )

        #store the course title of the course page
        course = driver.find_element(By.CLASS_NAME, "courseHeader--title").text

        #find the assignment table
        assignment_grouped = driver.find_element(By.TAG_NAME,'tbody')

        #Create a list of individual assingment elements
        assignments = assignment_grouped.find_elements(By.TAG_NAME, "tr")
        print("Scraping Assignments on Course Page") 

        #filter for assignments with No submissions
        assignments = filter(lambda assignment: has_no_submission(assignment), assignments)
        print("assignments filtered out now are ", assignments)


        #Scrape data from each assignment and organize it
        return [assignmentElementToEvent(assignment, course, href) for assignment in assignments]
    
    
    ##PROGRAM##
    #temp_dir = tempfile.mkdtemp()
    
    #creates the and assigns the appropriate driver
    driver = get_driver()
    logger.info(f"Driver Created {driver}")
    driver.delete_all_cookies()   

    if sys.platform in ["Linux", "darwin"]:
        cookie_path = get_path() / "cookies.pkl"
    else: #windows
        Win_folder_path = get_win_path()
        cookie_path = Win_folder_path / "cookies.pkl"
        
    # Load cookies if they exist
    if os.path.exists(cookie_path):
        print("Cookies exist, going to gradescope")
        # If you have cookies, go to the gradescope, load cookies, refresh and you should be logged in
        driver.get("https://www.gradescope.com")

        cookies = pickle.load(open(cookie_path, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        print("refreshing")
        driver.refresh()
        
        #Check if you loaded into gradescope successfully
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "courseList--term"))
            )
            print("we in gradescope")
            
        except TimeoutException:
            print("Need to mudd_login")
            
            login()
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "courseList--term"))
            )
            print("Homepage Loaded")   

    #no cookies need to log in        
    else:
        print("No cookies found, going to login ")
        login()
    
    # Save cookies to a file (For DuoPush)
    WebDriverWait(driver, 500).until(
        EC.presence_of_element_located((By.CLASS_NAME, "courseList--term"))
    )
    pickle.dump(driver.get_cookies(), open(cookie_path, "wb"))
    print("Cookies Saved")

    #Search for the first course list and make sure it is not an instructor course list
    if not ("Instructor Courses" in driver.find_element(By.ID, "account-show" ).text):
        #find the student course list
        courseList = driver.find_element(By.CLASS_NAME,'courseList--coursesForTerm')
    else:
        #if the fist courseList was an instructor course list use the second one which is a student course list
        courseLists = driver.find_elements(By.CLASS_NAME,'courseList')
        courseList = courseLists[1].find_element(By.CLASS_NAME,'courseList--coursesForTerm')

    print("courseList is", courseList)

    #Find all course boxes in the student course list
    courses = courseList.find_elements(By.CLASS_NAME, 'courseBox')

    #extract the course links from the course boxes
    print("courses are", courses)
    course_urls = [elem.get_attribute("href") for elem in courses]

    #Create an event dictionary for each course
    data = []
    for href in course_urls:
        if href:
            data.extend(assignment_scrape(href))
        
    print("FINAL OUTPUT YAY", data)
    return data
