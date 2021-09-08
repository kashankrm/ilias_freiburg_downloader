import time
from loguru import logger

class ElementParser:
    def __init__(self):
        pass
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
    def check_if_empty_page(self,driver):
        elem = driver.find_element_by_id("il_center_col")
        return elem.get_attribute("innerHTML").strip() == ""
        
    def parse(self, driver, element):
        try:
            #check if the page is empty
            if self.check_if_empty_page(driver):
                element.parsed = True
                return
            child_list = driver.find_element_by_class_name("ilContainerItemsContainer")
            childern = child_list.find_elements_by_class_name("ilObjListRow")
        except Exception as e:
            logger.error("exception occured!! "+str(e))
            element.parsed = False
            return
        for ch in childern:
            element.add_childern(ch)
        
        element.parsed = True
        
    def parse_video_link(self,driver,element):
        driver.open_link(element)
        time.sleep(2)
        video_element = driver.find_elements_by_tag_name('video')[0]
        element.link = video_element.get_attribute("src")
        tries = 10
        while tries>0 and element.link == "":
            time.sleep(1)
            element.link = video_element.get_attribute("src")
        if element.link == "":
            logger.error("empty link found at {}".format(element.get_parent_string()))
        driver.close_link(element)
    def start(self,driver,element):
        logger.debug("parser.start call on element {}".format(element.get_parent_string()))
        driver.open_link(element)
        time.sleep(2)
        self.parse(driver, element)
        traversable_children = [c for c in element.childern if c.type in ["Course","Folder"]]  
        video_links = [c for c in element.childern if c.type == 'Interactive Video']
        for vl in video_links:
            self.parse_video_link(driver,vl)

        for ch in traversable_children:
            if "Lectures" in ch.name or "05_b"  in ch.name:
                self.start(driver, ch)
            else:
                self.start(driver, ch)
        driver.close_link(element)
        time.sleep(2)
