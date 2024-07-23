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
#import chromedriver_autoinstaller
import warnings
import urllib3
import certifi
import urllib.request
import ssl
import logging
import os



logger = logging.getLogger(__name__)

def get_driver():
    logger = logging.getLogger(__name__)
    return driver_setup()

def make_executable(path):
    # Change the file permissions to make it executable
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)

def is_executable(file_path):
    # Check if the file is executable
    return os.path.isfile(file_path) and os.access(file_path, os.X_OK)   
    
    
def driver_setup():
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    # chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    # Find operating system's path to drivers/chromedriver
    driver_path = shutil.which('chromedriver')

    # Remove the folder and everything inside it if the path exists
    if driver_path:
        driver_folder = os.path.dirname(driver_path)
        shutil.rmtree(driver_folder)
    
    #Create Web Driver     
    try:
        #windows browser
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        from selenium.webdriver.edge.service import Service as EdgeService
        
        #options
        options = webdriver.EdgeOptions()
        options.addargument("--headless=new")
        
        #create driver
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service = service, options=options)
        
        return driver
    except Exception as e:
        try:
            def create_ssl_context():
                context = ssl.create_default_context(cafile=certifi.where())
                return context

            def install_chromedriver():
                # Create a custom opener with our SSL context
                context = create_ssl_context()
                opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
                urllib.request.install_opener(opener)
            
            install_chromedriver()
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print("fancy new thing didn't work")
            logger.info(f"ChromeDriverManager not working {e}")
            executable_path = ChromeDriverManager().install()
            if executable_path.endswith("THIRD_PARTY_NOTICES.chromedriver"):
                executable_path = executable_path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver")
            logger.info(f"ChromeDriverManager, {executable_path}")

            # Check if the executable_path leads to a document instead of an executable
            if not is_executable(executable_path):
                logger.warning(f"The file at {executable_path} is not executable. Attempting to fix permissions.")
                make_executable(executable_path)

            service = ChromeService(executable_path=executable_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver