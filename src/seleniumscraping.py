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
from macPath import get_path

def scraping():
    """
    Scrapes Gradescope for assignments and returns them as a list of events.

    Returns:
        (arr): An array of event dictionaries formated for the google calendar api
    """
    
    ##SETUP##
    
    temp_dir = tempfile.mkdtemp()
    # Configure Chrome options to run in headless mode
    chrome_options = webdriver.ChromeOptions()
    # # chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--remote-debugging-port=9222")  # Enable remote debugging
    chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    #Create Web Driver
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.delete_all_cookies()
    
    ##DEFINE FUNCTIONS##
    def purdueLogin(clientUsername, clientPassword):
        print("going to Purdue login page")
        driver.get("https://www.gradescope.com/login")
        # clientUsername = input("Enter your username: ")
        # clientPassword = input("Enter your password: ")
        # Find the username and password fields once page loads sufficiently
        username = WebDriverWait(driver, 500).until(
            EC.element_to_be_clickable((By.ID, "session_email"))  
        )
        password = driver.find_element(By.ID, "session_password")
        print("logging in", clientUsername, clientPassword)
        username.send_keys(clientUsername)
        password.send_keys(clientPassword)
        password.send_keys(Keys.RETURN)
            
    def muddLogin(clientUsername, clientPassword):
        print("going to muddLogin page")
        driver.get("https://www.gradescope.com/auth/saml/hmc")
        # Find the username and password fields once page loads sufficiently
        username = WebDriverWait(driver, 500).until(
            EC.element_to_be_clickable((By.ID, "identification"))  
        )
        password = driver.find_element(By.ID, "ember533") 

        # Submit credentials
        username.send_keys(clientUsername)
        password.send_keys(clientPassword)
        password.send_keys(Keys.RETURN)
            
        try:
            print("trying duo")
            duo()  
            print("looking for trust")
            trust = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.ID, "trust-browser-button"))  
            )
            print("ok found it")
            trust.click()
        except Error as e:
            print("oops missed it", e)
    
    #
    def login():
        school, clientUsername, clientPassword = ui()
        if school == "Harvey Mudd College":
            muddLogin(clientUsername, clientPassword)
        else:
            purdueLogin(clientUsername, clientPassword)

    def assignmentElementToEvent(assignment, course, defaultHref):
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
        assignmentPrimary = assignment.find_element(By.CLASS_NAME, "table--primaryLink")
        assignmentName = assignmentPrimary.text
        try:
            assignmentHref = assignmentPrimary.find_element(By.TAG_NAME, "a").get_attribute("href")
        except:
            assignmentHref = defaultHref
        print("link should be", assignmentHref)
        #get the assignmentDue Date
        try:
            dueDateElement = assignment.find_element(By.CLASS_NAME, "submissionTimeChart--dueDate")
        except:
            print("there's no due date for assignment {assignment}")
            return
        dueDateUnformatted = dueDateElement.get_attribute("datetime")

        # Change Due Date format to Google Calendar's format
        obj = datetime.strptime(dueDateUnformatted, '%Y-%m-%d %H:%M:%S %z')
        dueDate = obj.strftime("%Y-%m-%d") + "T" + obj.strftime("%H:%M:%S") + obj.strftime("%z")[0:3] + ':' + obj.strftime("%z")[3:5]

        # Create a start date 30 minutes before the assignment is due
        startDateObj = obj - timedelta(minutes=30)
        startDate = startDateObj.strftime("%Y-%m-%d") + "T" + startDateObj.strftime("%H:%M:%S") + startDateObj.strftime("%z")[0:3] + ':' + startDateObj.strftime("%z")[3:5]

        event = {
            'summary': course,
            'description': assignmentName + "\n" + assignmentHref,
            'colorId': "7",
            'start': {
                'dateTime': startDate,
            },
            'end': {
                'dateTime': dueDate,
            },
            'reminders': {
                'useDefault': True,
            },
        }
        print("event is", event)
        return event
    
    def has_no_submission(assignment):
        return "No Submission" in assignment.text

    def assignmentScrape(href):
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
        assignmentGrouped = driver.find_element(By.TAG_NAME,'tbody')

        #Create a list of individual assingment elements
        assignments = assignmentGrouped.find_elements(By.TAG_NAME, "tr")
        print("Scraping Assignments on Course Page") 

        #filter for assignments with No submissions
        assignments = filter(lambda assignment: has_no_submission(assignment), assignments)
        print("assignments filtered out now are ", assignments)


        #Scrape data from each assignment and organize it
        return [assignmentElementToEvent(assignment, course, href) for assignment in assignments]
    
    ##PROGRAM##
    if sys.platform in ["Linux", "darwin"]:
        cookie_path = get_path() / "cookies.pkl"
        # token_path = "../__file__"
    else:
        cookie_path = "cookies.pkl"
    # Load cookies if they exist
    if cookie_path.exists():
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
            print("Need to muddLogin")
            
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
        #If it is not an instructor course list then the first instance of the courseList is a student sourse list
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
    courseUrls = [elem.get_attribute("href") for elem in courses]

    #Create an event dictionary for each course
    data = []
    for href in courseUrls:
        print("course href is", href)
        if href:
            data.extend(assignmentScrape(href))
        
    print("FINAL OUTPUT YAY", data)
    return data