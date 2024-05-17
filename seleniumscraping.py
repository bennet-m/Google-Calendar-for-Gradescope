from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import pickle
import os


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
    driver.get("https://www.gradescope.com")  # Navigate to the root domain to set cookies
    cookies = pickle.load(open("cookies.pkl", "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)

    print("refreshing")
    driver.refresh()  # Refresh to apply cookies to the current session
    
    try:
        
        element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "courseList--term"))
        )
        # If the element is found, perform some action
        print("we in gradescope")
        
    except TimeoutException:
        print("Need to login")
        
        login()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "courseList--term"))  # Adjust based on expected element on the next page
        )
        print("Homepage Loaded bitch")     
else:
    print("No cookies found, going to login ")
    login()
    # Wait for the next page or interaction to complete
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "courseList--term"))  # Adjust based on expected element on the next page
    )
    print("Homepage Loaded")

# Save cookies to a file (For DuoPush)
driver.implicitly_wait(10)

pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
print("Cookies Saved")

# Retrieve and print the HTML content of the page
html_content = driver.page_source
soup = BeautifulSoup(html_content, 'html.parser')
print("HTML Source Collected")

#search for the most recent courseList
#courseList = soup.find('div', class_='courseList--term')
#print courseList

#courses = courseList.find_all("a", class_='courseBox')

courseList = driver.find_element(By.CLASS,'courseList--term')
courses = courseList.find_elements(By.CLASS, 'courseBox')

courseURLs=[tag.get_attribute('href') for tag in courses]

html_content = courses.page_source
coursesSoup = BeautifulSoup(html_content, 'html.parser')
print(coursesSoup)

##Garbage below I think
#courseUrls = [tag['href'] for tag in courses]
#rint(courseUrls)

# print("tags are", tags, "\n\n\n")
# urls = [tag['href'] for tag in tags]
# print(type(urls))


# course = locate_with(By.TEXT, "input").below({By.CLASS_NAME: "courseList--term"})
# print(course)

# Use a more accurate XPath to target the course links under 'Spring 2024'
# Adjust the XPath to select the following sibling of the div that contains "Spring 2024" which actually holds the course links.



#course_links = driver.find_elements(By.XPATH, "//div[contains(text(), 'Student Courses')]/following::div[contains(text(),'Spring 2024')]/following-sibling::div[1]//a")

# Extract href attributes
#hrefs = [link.get_attribute('href') for link in course_links]

# Print or process the links
#print(hrefs)