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
    def parse(self, driver, element):
        child_list = driver.find_element_by_class_name("ilContainerItemsContainer")
        childern = child_list.find_elements_by_class_name("ilObjListRow")
        for ch in childern:
            element.add_childern(ch)
        
        element.parsed = True
        
    def start(self,driver,element):
        logger.debug("parser.start call on element {}".format(element.get_parent_string()))
        driver.open_link(element)
        time.sleep(2)
        self.parse(driver, element)
        traversable_children = [c for c in element.childern if c.type in ["Course","Folder"]]  
        for ch in traversable_children:
            self.start(driver, ch)
        driver.close_link(element)
        time.sleep(2)
