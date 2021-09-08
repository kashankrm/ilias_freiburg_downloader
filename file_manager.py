from downloader import Downloader, MultiPartDownloader
import json
from loguru import logger
from threading import Lock, Thread
import os
class FileManager:
    def __init__(self):
        self.course_dict = {}
        self.downloader = Downloader()
        self.local_db_name = "local_files.json"
        self.local_db = []
        self.load_local_db()
        self.download_lock = Lock()
        self.local_db_lock = Lock()
        self.max_download_threads = 8
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
            files = [ch for ch in childern if ch.type in ["File","Interactive Video","Learning Module File"]]
            childern_files = [child  for ch in childern for child in get_all_files_recsive(ch)]
            return files + childern_files
        course = self.course_dict[course_name]
        files = get_all_files_recsive(course.course_element)
        return files
    def update_local_db(self):
        with self.local_db_lock:
            with open(self.local_db_name,"r+") as f:
                local_db = json.load(f)
            db_set = set(self.local_db) 
            diff = [x for x in local_db if x not in db_set]
            if len(diff)>0:
                logger.debug("writing following changes in local_db")
                logger.debug(f"changes are [{diff}]")
            with open(self.local_db_name,"w+") as f:
                json.dump(self.local_db,f)
    def load_local_db(self):
        if not os.path.exists(self.local_db_name):
            with open(self.local_db_name,"w+") as f:
                f.write("[]")
            
        with open(self.local_db_name,"r+") as f:
            self.local_db = json.load(f)
        
    def _download(self,driver,f):
        with self.download_lock:
            self.downloader.update_cookies(driver.get_cookies())
            already_downloaded = f.get_parent_string() in self.local_db
        if not already_downloaded:
            self.downloader.download(f)
            with self.download_lock:
                self.local_db.append(f.get_parent_string())
            self.update_local_db()
        else:
            logger.info("skipping file {} because it exists in db".format(f.name))
        
    def download_files(self, driver, course_name):
        def worker(f):
            self._download(driver,f)
        with self.downloader as _:
            files = self.get_all_files(course_name)
            # for f in files:
            #         self._download(driver,f)
            threads = []
            for f in files:
                t = Thread(target=worker,args=(f,))
                t.start()
                threads.append(t)
                if len(threads) >= self.max_download_threads:
                    thds=[]
                    for t in threads:
                        if t.is_alive():
                            thds.append(t)
                    if len(thds)>= self.max_download_threads:
                        threads[0].join()

                    else:
                        threads = thds
                    
                    
                # self._download(driver,f)
            for t in threads:
                t.join()
        
