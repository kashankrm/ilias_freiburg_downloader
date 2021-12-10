import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import warnings
from loguru import logger

class CustomDriver:
    def __init__(self, node, retries):
        self.retries = retries
        self.node = node
        self.active_handles = {}
        self.current_handle = None
        self.handle_stack = []

    def __getattribute__(self, name):
        from loguru import logger
        attr = super().__getattribute__(name)
        if hasattr(attr, "__call__"):
            def log_func(*args,**kwargs):
                logger.debug("called {} with {} and {}".format(name,args,kwargs))
                ret = attr(*args,**kwargs)
                return ret
            return log_func
        else:
            return attr
    def __getattr__(self, name):
        
        attr = self.node.__getattribute__(name)
        if hasattr(attr, '__call__'):
            def func(*args,**kwargs):
                tried = 0
                while tried < self.retries:
                    try:
                        ret = attr(*args,**kwargs)
                        return ret
                    except:
                        tried += 1
                        time.sleep(1)
                return attr(*args,**kwargs)
            return func
        else:
            return attr
    def find_elements_by_xpath(self,xpath):

        tried = 0

        while tried < self.retries:

            try:

                elems = self.node.find_elements_by_xpath(xpath)
                if len(elems) == 0:
                    raise RuntimeError("no elements found!")
                return elems

            except:
                tried += 1
                time.sleep(1)
        raise Exception('could not find element in {} tries'.format(self.retries))
    def find_elements_by_tag_name(self,tagname):

        tried = 0

        while tried < self.retries:

            try:

                elems = self.node.find_elements_by_tag_name(tagname)
                if len(elems) == 0:
                    raise RuntimeError("no elements found!")
                return elems

            except:
                tried += 1
                time.sleep(tried)
        raise Exception('could not find element in {} tries'.format(self.retries))
    def get_childern(self,elem):
        return elem.find_elements_by_xpath(".//*")
    def find_element_by_xpath(self,xpath):

        tried = 0

        while tried < self.retries:

            try:

                elem = self.node.find_element_by_xpath(xpath)
                if elem is None:
                    raise Exception("could not find element, returned None")
                return elem
                
            except:

                tried += 1
                time.sleep(1)
        raise Exception('could not find element in {} tries'.format(self.retries))
    def get(self, link):
        current_handle = self.node.current_window_handle
        self.active_handles["root"] = current_handle
        self.current_handle = "root"
        return self.node.get(link)
    def update_window_handles(self, handles, name):

        new_handle_found = list(set(handles) - set(self.active_handles.values()))
        if len(new_handle_found)>1:
            #TODO: add url to warnings
            warnings.warn("Warning: found multiple new handles url")
            new_handle = new_handle_found[-1]
        else:
            new_handle = new_handle_found[0]
        self.active_handles[name] = new_handle
        return new_handle
    def open_link(self, element):
        logger.debug("openning link {}".format(element.get_parent_string()))
        address = element.link
        self.node.execute_script("window.open('{}')".format(address))
        WebDriverWait(self.node, 10).until(EC.number_of_windows_to_be(len(self.active_handles)+1))
        handle_name = element.get_parent_string()
        new_handle = self.update_window_handles(self.node.window_handles, handle_name)
        self.handle_stack.append(self.current_handle)
        self.current_handle = handle_name
        self.node.switch_to_window(new_handle)

        return
    def close_link(self, element):
        logger.debug("closing link {}".format(element.get_parent_string()))
        
        handle_name = element.get_parent_string()
        if handle_name not in self.active_handles:
            warnings.warn("Warning: tried to close a link that does not exists -> {}".format(handle_name))
            return
        current_window = self.node.current_window_handle
        if current_window != self.active_handles[handle_name]:
            self.node.switch_to_window(self.active_handles[handle_name])
        self.node.close()
        if len(self.handle_stack) > 0:
            last_handle = self.handle_stack.pop()
        else:
            warnings.warn("warning: attempt to pop from handle stack when len = 0")
            last_handle = "root"
        self.node.switch_to_window(self.active_handles[last_handle])
        self.current_handle = last_handle
        del self.active_handles[handle_name]
        return
        



        

