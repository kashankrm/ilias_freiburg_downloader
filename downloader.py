import requests
import os


class Downloader:
    def __init__(self):
        self.root_path = os.path.join(os.getcwd(),"downloaded_files")
        self.session = requests.Session()
        self.cookies = {}
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
    def add_cookie(self,cookie):
        self.session.cookies.set(cookie["name"], cookie['value'])
        self.cookies[cookie["name"]] = cookie['value']
    def update_cookies(self,cookies):
        for cookie in cookies:
            if self.cookies[cookies['name']] is None:
                self.add_cookie(cookie)
    def download(self, link):
        parent_dirs = link.get_parent_string().split("/@/")
        download_folder = os.path.join(self.root_path,"/".join(parent_dirs[:-1]))
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        with self.session.get(link.link, stream=True) as r:
            r.raise_for_status()
            with open(os.path.join(download_folder,parent_dirs[-1]),"wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

    