from downloader import Downloader
class FileManager:
    def __init__(self):
        self.course_dict = {}
        self.downloader = Downloader()
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
    def add_course_list(self,course_list):
        for course in course_list:
            self.course_dict[course.name] = course
    def get_all_files(self, course_name):
        def get_all_files_recsive(course_element ):
            childern = course_element.childern
            files = [ch for ch in childern if ch.type == "File"]
            childern_files = [child  for ch in childern for child in get_all_files_recsive(ch)]
            return files + childern_files
        course = self.course_dict[course_name]
        files = get_all_files_recsive(course.course_element)
    def download_files(self, driver, course_name):
        files = self.get_all_files(course_name)
        f = files[0]
        self.downloader.update_cookies(driver.get_cookies())
        self.downloader.download(f)
