from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta
import pickle
import os

def scraping():
    """
    Scrapes Gradescope for assignments and returns them as a list of events.

    Returns:
        (arr): An array of event dictionaries formated for the google calendar api
    """
    #Create Web Driver
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    def login():
        print("going to login page")
        driver.get("https://www.gradescope.com/auth/saml/hmc")
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        # Find the username and password fields once page loads sufficiently
        username = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "identification"))  
        )
        password = driver.find_element(By.ID, "ember533") 

        # Submit credentials
        username.send_keys(username)
        password.send_keys(password)
        password.send_keys(Keys.RETURN)
        
    # Load cookies if they exist
    if os.path.exists("cookies.pkl"):
        print("Cookies exist, going to gradescope")
        # If you have cookies, go to the gradescope, load cookies, refresh and you should be logged in
        driver.get("https://www.gradescope.com")  
        cookies = pickle.load(open("cookies.pkl", "rb"))
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
            print("Need to login")
            
            login()
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "courseList--term"))
            )
            print("Homepage Loaded")   

    #no cookies need to log in        
    else:
        print("No cookies found, going to login ")
        login()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "courseList--term"))
        )
        print("Homepage Loaded")

    # Save cookies to a file (For DuoPush)
    driver.implicitly_wait(10)
    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    print("Cookies Saved")

    #Search for the first course list and make sure it is not an instructor course list
    if not (driver.find_element(By.XPATH, "//*[@id='account-show']/h1[1]" ).text == "Instructor Courses"):
        #If it is not an instructor course list then the first instance of the courseList is a student sourse list
        #find the student course list
        courseLists = driver.find_elements(By.CLASS_NAME,'courseList--coursesForTerm')
        print(courseLists.text)
        #Find all course boxes in the student course list
        courses = courseLists.find_elements(By.CLASS_NAME, 'courseBox')
    else:
        #if the fist courseList was an instructor course list use the xpath to skip to the second course list which is a student course list
        courseLists = driver.find_element(By.XPATH,"//*[@id='account-show']/div[3]/div[2]")
        print(courseLists.text)
        #Find all course boxes in the student course list
        courses = courseLists.find_elements(By.CLASS_NAME, 'courseBox')

    #extract the course links from the course boxes
    courseUrls = [elem.get_attribute("href") for elem in courses]

    def assignmentElementToEvent(assignment, course):
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
        assignmentHref = assignmentPrimary.find_element(By.TAG_NAME, "a").get_attribute("href")
        print("link should be", assignmentHref)
        #get the assignmentDue Date
        dueDateElement = assignment.find_element(By.CLASS_NAME, "submissionTimeChart--dueDate")
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


    ##TODO: Make the assignment scrape only look at future assignments##
    def assignmentScrape(href):
        '''
        Scrapes a Gradescope course page for assignments for the current user date
        and organizes the data into an array of event dictionaries.

        Args:
            href (str): Gradescope course href string as an input

        Returns:
            (arr): An array of event dictionaries formated for the google calendar api
        '''

        #get the course page
        driver.get(href)

        #wait for it to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "courseHeader--title"))
        )

        #store the course title of the course page
        course = driver.find_element(By.CLASS_NAME, "courseHeader--title").text

        #find the assignments
        assignmentGrouped = driver.find_element(By.TAG_NAME,'tbody')

        #Create a list of assingment elements
        assignments = assignmentGrouped.find_elements(By.TAG_NAME, "tr")
        print("Scraping Assignments on Course Page") 

        #Scrape data from each assignment and organize it
        return [assignmentElementToEvent(assignment, course) for assignment in assignments[:3]]
    
    #Create an event dictionary for each course
    data = []
    for href in courseUrls[:3]:
        data.extend(assignmentScrape(href))
        
    print("FINAL OUTPUT YAY", data)
    return data