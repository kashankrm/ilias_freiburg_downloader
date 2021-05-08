import requests
import os


class Downloader:
    def __init__(self,cookies):
        self.root_path = os.getcwd()
        self.session = requests.Session()
        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])
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

    