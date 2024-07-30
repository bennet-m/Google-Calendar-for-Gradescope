import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import logging
import os
import sys
import stat
from webdriver_manager.core.driver_cache import DriverCacheManager
from macPath import *
import chromedriver_autoinstaller

logger = logging.getLogger(__name__)

def get_driver():
    if sys.platform in ["Linux", "darwin"]:
        try:
            return chrome_driver_setup()
        except Exception as e:
            logger.info(f"{e} \n \n Tried everything and it's not working. Now attempting to remove driver and reinstall. \n")
            driver_path = shutil.which('chromedriver')
            # Remove the folder and everything inside it if the path exists
            if driver_path:
                driver_folder = os.path.dirname(driver_path)
                shutil.rmtree(driver_folder)
            return chrome_driver_setup()
    elif sys.platform == "win32":
        return bing_driver_setup()

def chrome_driver_setup():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

    def make_executable(path):
        # Change the file permissions to make it executable
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC)

    def is_executable(file_path):
        # Check if the file is executable
        return os.path.isfile(file_path) and os.access(file_path, os.X_OK)   

    def third_party_notice_correction(executable_path):
        # need to do this because it installs incorrectly sometimes
        if executable_path.endswith("THIRD_PARTY_NOTICES.chromedriver"):
            executable_path = executable_path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver")
        logger.info(f"ChromeDriverManager, {executable_path}")
        if not is_executable(executable_path):
            logger.info(f"The file at {executable_path} is not executable. Attempting to fix permissions.")
            make_executable(executable_path)
    
    # I know this is disgusting. Please blame ChromeDriver and Pyinstaller with MacOS because they don't work well together
    try:
        #Mac needs the apps resources to be in a specific location for .app applications
        logger.info(f"Trying mac path method")
        install_path = get_path()
        
        #Using Cache manager to specify path to be in the Mac Resource Path
        cache_manager=DriverCacheManager(install_path)
        
        executable_path = ChromeDriverManager(cache_manager=cache_manager).install()
        if executable_path.endswith("THIRD_PARTY_NOTICES.chromedriver"):
            executable_path = executable_path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver")
        logger.info(f"ChromeDriverManager before correction, {executable_path}")
        third_party_notice_correction(executable_path)
        logger.info(f"ChromeDriverManager after correction, {executable_path}")

        
        driver = webdriver.Chrome(service=ChromeService(executable_path), options=chrome_options)
        return driver
    except Exception as e:
        try: 
            logger.info(f"{e} \n \n Error. Attempting default chrome webdriver setup \n")
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e: 
            try: 
                logger.info(f"{e} \n \n Error. Attempting other default chrome webdriver setup: \n")
                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                return driver
            except Exception as e:
                try: 
                    logger.info(f"{e} \n \n Error. Attempting autoinstaller: \n")
                    chromedriver_autoinstaller.install()
                    driver = webdriver.Chrome()
                    return driver
                except Exception as e:
                    try:
                        logger.info(f"{e} \n \n ChromeDriver not working. trying ChromeDriverManager().install() \n")
                        executable_path = ChromeDriverManager().install()
                        third_party_notice_correction(executable_path)
                        driver = webdriver.Chrome(options=chrome_options)
                        return driver
                    except Exception as e:
                        try:
                            logger.info(f"{e} \n \n ChromeDriver not working. Trying basic install for Selinium 4.11V \n")
                            driver = webdriver.Chrome()
                            return driver
                        except Exception as e:
                            try:
                                logger.info(f"{e} \n \n Erm Maybe Bing on Mac will work????... \n")
                                #windows browser (idk at this point MAC blows, in the bad way)
                                from webdriver_manager.microsoft import EdgeChromiumDriverManager
                                from selenium.webdriver.edge.service import Service as EdgeService
                                
                                #options
                                options = webdriver.EdgeOptions()
                                options.add_argument("--headless=new")
                                
                                #create driver
                                service = EdgeService(EdgeChromiumDriverManager().install())
                                driver = webdriver.Edge(service = service, options=options)
                                
                                return driver
                            except Exception as e:
                                try:
                                    logger.info(f"{e} \n \n trying chromedriver_py... \n")
                                    from chromedriver_py import binary_path # this will get you the path variable
                                    svc = webdriver.ChromeService(executable_path=binary_path)
                                    driver = webdriver.Chrome(service=svc)           
                                except Exception as e:
                                    logger.info(f"{e} \n \n All Driver Initialization Attempts Failed \n")

def bing_driver_setup():
    try:
        #windows browser
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        from selenium.webdriver.edge.service import Service as EdgeService
        
        #options
        options = webdriver.EdgeOptions()
        options.add_argument("--headless=new")
        
        #create driver
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service = service, options=options)
        
        return driver
    
    except Exception as e:
        logger.info(f"{e} \n \n EdgeDriverManager not worki\n")
        logger.info(f"Trying Chrome")
        
        return chrome_driver_setup()

