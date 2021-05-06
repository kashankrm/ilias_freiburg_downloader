import time

class CustomDriver:
    def __init__(self, node, retries):
        self.retries = retries
        self.node = node

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
