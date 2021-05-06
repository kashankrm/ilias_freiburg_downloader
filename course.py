

class Course:
    def __init__(self,elem):
        self.course_obj = elem
        self.type = elem.find_element_by_xpath("div/div/div/img").get_attribute("alt")
        try:
            self.link = elem.find_element_by_xpath("div/div/div[2]/div/div[1]/h4/a")
            self.course_name = self.link.get_attribute("innerHTML")
        except:
            self.link = ""
            self.course_name = elem.find_element_by_xpath("div/div/div[2]/div/div[1]/h4").get_attribute("innerHTML")

        try:
            self.description = elem.find_element_by_xpath("div/div/div[2]/div/div[4]").get_attribute("innerHTML")
        except:
            self.description = ""
        try:
            self.availability = elem.find_element_by_xpath("div/div/div[2]/div/div[5]/span[2]").get_attribute("innerHTML")
        except:
            self.availability = ""
        try:
            self.period_of_event = elem.find_element_by_xpath("div/div/div[2]/div/div[5]/span[1]").get_attribute("innerHTML")
        except:
            self.period_of_event = ""
    def click(self):
        self.link.click()
        
    