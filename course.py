import json
class Course:
    def __init__(self,elem):
        self.course_obj = elem
        self.course_element = CourseElement(elem.find_element_by_xpath("div"))
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
        return self.course_element.__getattribute__(name)
        
class CourseElement:
    def __init__(self, root, parent=None):
        if parent is None:
            self.parent = parent
            elem = root.find_element_by_class_name("media-body")
            self.root = elem
            
            self.childern = []
            self.parsed = False
            self.type = root.find_element_by_tag_name("img").get_attribute("alt")
            try:
                link_div = elem.find_element_by_class_name("il-item-title")
                self.link = link_div.find_element_by_xpath("a").get_attribute("href")
                self.name = link_div.find_element_by_xpath("a").get_attribute("innerHTML")
            except:
                self.link = ""
                self.name = elem.find_element_by_class_name("il-item-title").get_attribute("innerHTML")

            try:
                self.description =  elem.find_element_by_class_name("il-item-description")
            except:
                self.description = ""
            try:
                self.availability = elem.find_element_by_xpath("div/div[2]/div/div[5]/span[2]").get_attribute("innerHTML")
            except:
                self.availability = ""
            try:
                self.period_of_event = elem.find_element_by_xpath("div/div[2]/div/div[5]/span[1]").get_attribute("innerHTML")
            except:
                self.period_of_event = ""
        else:
            self.parent = parent
            self.root = root
            elem = root
            self.childern = []
            self.parsed = False
            self.type = elem.find_element_by_xpath("div/div[1]/img").get_attribute("alt")
            try:
                a_tag = elem.find_elements_by_tag_name("a")[0]
                self.link = a_tag.get_attribute("href")
                self.name = a_tag.get_attribute("innerHTML")
            except:
                self.link = ""
                self.name = elem.find_element_by_xpath("div/div[2]/div/div[1]/h4").get_attribute("innerHTML")

            try:
                self.description = elem.find_element_by_xpath("div/div[2]/div/div[4]").get_attribute("innerHTML")
            except:
                self.description = ""
            try:
                self.availability = elem.find_element_by_xpath("div/div[2]/div/div[5]/span[2]").get_attribute("innerHTML")
            except:
                self.availability = ""
            try:
                self.period_of_event = elem.find_element_by_xpath("div/div[2]/div/div[5]/span[1]").get_attribute("innerHTML")
            except:
                self.period_of_event = ""
    def __str__(self):
        return self.name + "/#/" +self.type
    def __repr__(self):
        obj = {}
        obj["name"] = self.name
        obj["type"] = self.type
        obj["link"] = self.link
        obj["desc"] = self.description
        obj["aval"] = self.availability
        obj["poev"] = self.period_of_event
        obj["childern"] = [repr(o) for o in self.childern]
        obj["parent"] = self.parent.name if self.parent is not None else "None"
        return json.dumps(obj)
    def add_childern(self, child):
         self.childern.append(CourseElement(child,self))

    def get_structure(self):
        structure = {}
        children_structure = []
        for ch in self.childern:
            children_structure.append(ch.get_structure())
        structure[self.name] = children_structure
        return structure
    def get_parent_string(self):
        return  self.parent.get_parent_string() + "/@/" + self.name if self.parent is not None else self.name

        