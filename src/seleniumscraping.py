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
import pickle
import os
import tempfile
import sys
from pathlib import Path
from macPath import *

#logger
import logging
logger = logging.getLogger(__name__)

def scraping():
    """
    Scrapes Gradescope for assignments and returns them as a list of events.

    Returns:
        (arr): An array of event dictionaries formated for the google calendar api
    """
    
    temp_dir = tempfile.mkdtemp()
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    #Create Web Driver
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.delete_all_cookies()
    
    ##DEFINE FUNCTIONS##
    def purdue_login(client_username, client_password):
        logger.info("going to Purdue login page")
        driver.get("https://www.gradescope.com/login")
        # Find the username and password fields once page loads sufficiently
        username = WebDriverWait(driver, 500).until(
            EC.element_to_be_clickable((By.ID, "session_email"))  
        )
        password = driver.find_element(By.ID, "session_password")
        logger.info("logging in", client_username, client_password)
        username.send_keys(client_username)
        password.send_keys(client_password)
        password.send_keys(Keys.RETURN)
            
    def mudd_login(client_username, client_password):
        logger.info("going to mudd_login page")
        driver.get("https://www.gradescope.com/auth/saml/hmc")
        # Find the username and password fields once page loads sufficiently
        username = WebDriverWait(driver, 500).until(
            EC.element_to_be_clickable((By.ID, "identification"))  
        )
        password = driver.find_element(By.ID, "ember533") 

        # Submit credentials
        username.send_keys(client_username)
        password.send_keys(client_password)
        password.send_keys(Keys.RETURN)
            
        try:
            logger.info("trying duo")
            duo()  
            logger.info("looking for trust")
            trust = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "trust-browser-button"))  
            )
            logger.info("ok found it")
            trust.click()
        except Error as e:
            logger.info("oops missed it", e)
    
    #No loop login
    # def login():
    #     school, client_username, client_password = ui()
    #     if school == "Harvey Mudd College":
    #         mudd_login(client_username, client_password)
    #     else:
    #         purdue_login(client_username, client_password)
    
    #login Loop   
    def login():
        while True:
            school, client_username, client_password = ui()
            if school == "Harvey Mudd College":
                mudd_login(client_username, client_password)
                try:
                    logger.info("testing to see if password is right")
                    driver.find_element(By.CLASS_NAME, "courseList--term")
                    
                    logger.info("Correct User Loggin")
                    break
                except:
                    #Notify user of incorrect information
                    incorrect_login()
                    logger.info("Incorrect User Info")
                    
            else:
                purdue_login(client_username, client_password)
                try:
                    logger.info("testing to see if password is right")
                    driver.find_element(By.CLASS_NAME, "courseList--term")
                    
                    logger.info("Correct User Loggin")
                    break
                except:
                    #Notify user of incorrect information
                    incorrect_login()
                    logger.info("Incorrect User Info")

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
        logger.info("link should be", assignment_href)
        #get the assignmentDue Date
        try:
            due_date_element = assignment.find_element(By.CLASS_NAME, "submissionTimeChart--dueDate")
        except:
            logger.info("there's no due date for assignment {assignment}")
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
        logger.info("event is", event)
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
        logger.info("Scraping Assignments on Course Page") 

        #filter for assignments with No submissions
        assignments = filter(lambda assignment: has_no_submission(assignment), assignments)
        logger.info("assignments filtered out now are ", assignments)


        #Scrape data from each assignment and organize it
        return [assignmentElementToEvent(assignment, course, href) for assignment in assignments]
    
    
    ##PROGRAM##
    if sys.platform in ["Linux", "darwin"]:
        cookie_path = get_path() / "cookies.pkl"
    else: #windows
        Win_folder_path = get_WinPath() / "GradeSync"
        cookie_path = Win_folder_path / "cookies.pkl"
        
    # Load cookies if they exist
    if os.path.exists(cookie_path):
        logger.info("Cookies exist, going to gradescope")
        # If you have cookies, go to the gradescope, load cookies, refresh and you should be logged in
        driver.get("https://www.gradescope.com")

        cookies = pickle.load(open(cookie_path, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        logger.info("refreshing")
        driver.refresh()  
        
        #Check if you loaded into gradescope successfully
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "courseList--term"))
            )
            logger.info("we in gradescope")
            
        except TimeoutException:
            logger.info("Need to mudd_login")
            
            login()
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "courseList--term"))
            )
            logger.info("Homepage Loaded")   

    #no cookies need to log in        
    else:
        logger.info("No cookies found, going to login ")
        login()
    
    # Save cookies to a file (For DuoPush)
    WebDriverWait(driver, 500).until(
                EC.presence_of_element_located((By.CLASS_NAME, "courseList--term"))
            )
    pickle.dump(driver.get_cookies(), open(cookie_path, "wb"))
    logger.info("Cookies Saved")

    #Search for the first course list and make sure it is not an instructor course list
    if not ("Instructor Courses" in driver.find_element(By.ID, "account-show" ).text):
        #If it is not an instructor course list then the first instance of the courseList is a student sourse list
        #find the student course list
        courseList = driver.find_element(By.CLASS_NAME,'courseList--coursesForTerm')
    else:
        #if the fist courseList was an instructor course list use the second one which is a student course list
        courseLists = driver.find_elements(By.CLASS_NAME,'courseList')
        courseList = courseLists[1].find_element(By.CLASS_NAME,'courseList--coursesForTerm')

    logger.info("courseList is", courseList)

    #Find all course boxes in the student course list
    courses = courseList.find_elements(By.CLASS_NAME, 'courseBox')

    #extract the course links from the course boxes
    logger.info("courses are", courses)
    course_urls = [elem.get_attribute("href") for elem in courses]

    #Create an event dictionary for each course
    data = []
    for href in course_urls:
        logger.info("course href is", href)
        if href:
            data.extend(assignment_scrape(href))
        
    logger.info("FINAL OUTPUT YAY", data)
    return data