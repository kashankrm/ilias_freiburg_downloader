from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
import warnings
import json
import time
import os
from loguru import logger

from course import Course
from webelement import CustomDriver
from custom_parser import ElementParser
from downloader import Downloader
from file_manager import FileManager
import sys

if os.path.exists("config.json"):

    with open("config.json") as f:

        config = json.load(f)

else:

    config = {}

class Login:

    def __init__(self):

        self.ilias_link = "https://ilias.uni-freiburg.de"

        self.gecko_path = "E:\\geckodriver.exe"

        self.course_list = []

        self.config = {}

        self.config["interested_course"] = "Maschinelles Lernen in den Lebenswissenschaften / Machine Learning in Life Science (-)"

        self.retries = 100
        self.fm = FileManager()
        logger.remove()
        logger.add(sys.stderr, level="INFO")


        # prox = Proxy()
        # prox.proxy_type = ProxyType.MANUAL
        # prox.http_proxy = "localhost:8081"

        capabilities = webdriver.DesiredCapabilities.FIREFOX
        # capabilities['marionette'] = True
        # prox.add_to_capabilities(capabilities)

        self.driver = CustomDriver(webdriver.Firefox(executable_path=self.gecko_path,desired_capabilities=capabilities),self.retries)
        def __getattribute__(self, name):
            attr = super().__getattribute__(name)
            if hasattr(attr, "__call__"):
                def log_func(*args,**kwargs):
                    logger.debug("called {} with {} and {}".format(name,args,kwargs))
                    ret = attr(*args,**kwargs)
                    return ret
                return log_func
            else:
                return attr
    def start(self):
        logger.debug("starting...")
        self.load_passwd()
        logger.debug("credentials loaded")
        self.driver.get(self.ilias_link)
        logger.debug("webpage loaded")
        self.authenticate()
        logger.debug("authentication complete")
        return
        

    def authenticate(self):

        clickbtn = self.find_login_btn()
                                     
        clickbtn.click()

        time.sleep(1)

        username_field = self.get_element('//*[@id="LoginForm_username"]')

        username_field.send_keys(self.user_auth["username"])

        password_field = self.get_element('//*[@id="LoginForm_password"]')

        password_field.send_keys(self.user_auth["password"])

        self.get_element('/html/body/div/div[3]/div[5]/div/div/form/div[3]/input').click()

        time.sleep(2)

    
    def find_login_btn(self):
        try:
            
            a_tags = self.driver.find_elements_by_tag_name("a")
            a_tags = [a for a in a_tags if a.get_attribute("href") is not None and "shib_login.php?target=" in a.get_attribute("href")  ]
            return a_tags[0]
            
        except:
            warnings.warn("could not find login button, trying xpath")
            login_btn = self.get_element("/html/body/div[4]/div/div/div[4]/div/div/div/div[2]/div[2]/div[1]/div/div[2]/div/form/div[2]/div/p/a")
            return login_btn
    def load_courses(self):

        course_list_obj = self.get_elements("/html/body/div[3]/div/div/div[5]/div/div/div/div[3]/div[3]/div/div[1]/div/div/*")

        self.course_list = []

        for course in course_list_obj:

            if course.get_attribute("class") == "ilObjListRow":

                self.course_list.append(Course(course))

        print([c.name for c in self.course_list])
        logger.debug("course loaded")
        logger.debug("\n".join([c.name for c in self.course_list]))
        
        
    
    def parse(self):
        parser = ElementParser()
        interested_course = next(c for c in self.course_list if self.config["interested_course"] in c.name)
        
        parser.start(self.driver,interested_course.course_element)
        print(repr(interested_course.course_element))
        self.fm.add_course_list(self.course_list)
        self.fm.download_files(self.driver, self.config["interested_course"])
        
        print("done")

    def get_element(self, xpath):
        return self.driver.find_element_by_xpath(xpath)
    
    def get_elements(self, xpath):
        return self.driver.find_elements_by_xpath(xpath)
        
    def load_passwd(self):

        with open("passwd.json") as f:

            self.user_auth = json.load(f)
        





def update_config(config):

    with open("config.json") as f:

        json.dump(config, f)




if __name__ == "__main__":

    login = Login()
    login.start()
    login.load_courses()
    login.parse()
