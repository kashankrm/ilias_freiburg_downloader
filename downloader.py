import requests
import os
from loguru import logger
import mimetypes
import string
from threading import Thread, Lock
from queue import Queue
from tempfile import TemporaryDirectory
import random
import time
import atexit
import copy


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
    def __enter__(self):
        pass
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def get_valid_filename(self,fn):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        return ''.join(c for c in fn if c in valid_chars)
    def add_cookie(self,cookie):
        self.session.cookies.set(cookie["name"], cookie['value'])
        self.cookies[cookie["name"]] = cookie['value']

    def update_cookies(self,cookies):
        for cookie in cookies:
            if self.cookies.get(cookie['name']) is None:
                self.add_cookie(cookie)
    
    def get_file_extension(self,mime):
        if ";" in mime:
            mime = mime.split(";")[0]
        if mime == "text/plain":
            return ".txt"
        else:
            return mimetypes.guess_extension(mime)

    def download(self, link):
        
        def _download(file_path,link,download_from_bytes=0,mode='wb'):
            if mode == 'ab':
                resume_header = {'Range': 'bytes=%d-' % download_from_bytes}
            else:
                resume_header = {}
            downloaded_bytes = 0
            try:
                with self.session.get(link, stream=True,headers=resume_header) as r:
                    r.raise_for_status()
                    with open(file_path,mode) as f:
                        for chunk in r.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
                                downloaded_bytes = downloaded_bytes + len(chunk)
            except Exception as e:
                logger.warning("exception occured "+str(e))

            return downloaded_bytes
        
        try:
            headers = self.session.head(link.link)
        except Exception as e:
            logger.error("following exception occured "+str(e))
            return
        content_size = int(headers.headers._store.get("content-length")[1])
        content_type = headers.headers._store.get("content-type")[1]
        file_ext = self.get_file_extension(content_type)
        logger.info("downloading file {} size {} type {}".format(link.name,content_size,content_type))
        
        parent_dirs = link.get_parent_string().split("/@/")
        parent_dirs = [self.get_valid_filename(x) for x in parent_dirs]
        download_folder = os.path.join(self.root_path,"/".join(parent_dirs[:-1]))
        file_name = self.get_valid_filename(parent_dirs[-1]+file_ext)
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        file_path = os.path.join(download_folder,file_name)
        bytes_downloaded = _download(file_path,link.link)
        tries = 10
        while bytes_downloaded < content_size and tries>0:
            logger.warning("downloading {} interuppted {} bytes out of {} bytes downloaded, retrying...".format(link.name,bytes_downloaded,content_size))
            bd = _download(file_path,link.link,bytes_downloaded,mode="ab")
            bytes_downloaded += bd
            tries -=1
        
        if bytes_downloaded < content_size:
            logger.error("error downloading file {} type {}".format(link.name,content_type))
            print("error we have a problem!!")

class MultiPartDownloader(Downloader):
    def __init__(self,num_worker=8,progress_bar=True) -> None:
        super().__init__()
        self.num_worker = num_worker
        self.progress_bar = progress_bar
        
    def __enter__(self):
        print("enter start")
        self.packet_size = 1024*1024
        self.exit_lock = Lock()
        self.exit_flag = False
        self.jobs_lock = Lock()
        self.jobs_queue = Queue()
        self.workers = []
        self.jobs = {}
        self.tmp_dir = TemporaryDirectory()
        for _ in range(self.num_worker):
            self.make_worker()
        print("enter stop")
    def _download(self,file_path,link,download_bytes_required=-1,download_from_bytes=0,mode='wb'):
        resume_header = {'Range': 'bytes=%d-' % download_from_bytes}
        downloaded_bytes = 0
        if download_bytes_required == -1:
            download_bytes_required=self.packet_size
        try:
            with self.session.get(link, stream=True,headers=resume_header) as r:
                r.raise_for_status()
                with open(file_path,mode) as f:
                    for chunk in r.iter_content(chunk_size=self.packet_size//10):
                        if chunk:
                            
                            downloaded_bytes = downloaded_bytes + len(chunk)
                            if downloaded_bytes >download_bytes_required:
                                excess = downloaded_bytes - download_bytes_required
                                f.write(chunk[:-excess])
                                downloaded_bytes -= excess
                                break
                            else:
                                f.write(chunk)
                            

        except Exception as e:
            logger.warning("exception occured "+str(e))
        return downloaded_bytes

    def _download_reliable(self,file_path,link,content_size,download_from_bytes=0):
        bytes_downloaded = self._download(file_path,link,content_size,download_from_bytes,mode='wb')
        tries = 10
        while bytes_downloaded < content_size and tries>0:
            logger.warning("downloading {} interuppted {} bytes out of {} bytes downloaded, retrying...".format(link,bytes_downloaded,content_size))
            bd = self._download(file_path,link,content_size-bytes_downloaded,download_from_bytes+bytes_downloaded,mode="ab")
            bytes_downloaded += bd
            tries -=1
        if bytes_downloaded < content_size:
            return False
        return True
        

    def make_worker(self):
        def worker():
            while True:
                with self.exit_lock:
                    if self.exit_flag:
                        return
                if self.jobs_queue.empty():
                    time.sleep(2)
                    continue
                
                job = self.jobs_queue.get(block=False)
                job_no = job["job_no"]
                file_path = job["file_path"]
                link = job["link"]
                download_from_bytes= job["download_from_bytes"]
                content_size = job["content_size"]
                result = self._download_reliable(file_path,link,content_size,download_from_bytes)
                with self.jobs_lock:
                    self.jobs[job_no]["result"] = result


        t = Thread(target=worker)
        t.start()
        self.workers.append(t)
    def print_progress(self,name,progress):
        if self.progress_bar:
            
            print("[{}] Progress {:2.1%}".format(name,progress), end="\r")
        
    def get_job_status(self, jobs):
        with self.jobs_lock:
            res = [self.jobs[j].get("result") for j in jobs]
        done_arr = [j is not None for j in res]
        done = all(done_arr)
        successful = all([j for j in res]) if done else False
        return done,successful,sum(done_arr)/len(done_arr)
    
    def download(self,link):
        try:
            headers = self.session.head(link.link)
        except Exception as e:
            logger.error("exception occured when getting head "+str(e))
            return

        content_size = int(headers.headers._store.get("content-length")[1])
        content_type = headers.headers._store.get("content-type")[1]
        file_ext = self.get_file_extension(content_type)
        logger.info("downloading file {} size {} type {}".format(link.name,content_size,content_type))
        
        parent_dirs = link.get_parent_string().split("/@/")
        parent_dirs = [self.get_valid_filename(x) for x in parent_dirs]
        download_folder = os.path.join(self.root_path,"/".join(parent_dirs[:-1]))
        file_name = self.get_valid_filename(parent_dirs[-1]+file_ext)
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        file_path = os.path.join(download_folder,file_name)

        
        all_jobs = []
        
        for idx in range(0,content_size,self.packet_size):
            if idx+self.packet_size > content_size:
                part_size = content_size - idx
            else:
                part_size = self.packet_size
            
            download_from_bytes = idx
            job_no = random.randint(1000,1000000000000)
            while job_no in self.jobs:
                job_no = random.randint(1000,100000000000)    
            rand_name = "ilas_downloader_{}".format(job_no)
            part_file_path = os.path.join(self.tmp_dir.name,rand_name)
            job = {
                "job_no":job_no,
                "file_path":part_file_path,
                "download_from_bytes":download_from_bytes,
                "link":link.link,
                "content_size":part_size
            }
            with self.jobs_lock:
                self.jobs[job_no] = job
            self.jobs_queue.put(copy.deepcopy(job))
            all_jobs.append(job_no)
        done = self.get_job_status(all_jobs)[0]
        while not done:
            done,_,progress = self.get_job_status(all_jobs)
            self.print_progress(link.name,progress)
            time.sleep(2)
        success = self.get_job_status(all_jobs)[1]
        if not success:
            logger.error("error downloading file {} type {}".format(link.name,content_type))
            
        else:
            self.stitch_file(all_jobs,file_path)


        
    def stitch_file(self,all_jobs,file_path):
        
        jobs = []
        with self.jobs_lock:
            for j in all_jobs:
                jobs.append(self.jobs[j])
        part_files = [j["file_path"] for j in jobs]
        with open(file_path,"wb") as f:
            for fp in part_files:
                with open(fp,"rb") as part:
                    f.write(part.read())
        
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        
        with self.exit_lock:
            self.exit_flag = True
        for t in self.workers:
            t.join()
        self.tmp_dir.cleanup()