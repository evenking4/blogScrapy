import threading
from scrapy import signals
import time
import logging

ExtensionLog = logging.getLogger("Extension")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
ExtensionLog.addHandler(stream_handler)

class LockManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_lock = False

    def acquire(self):
        self.lock.acquire()
        self.is_lock = True

    def release(self):
        self.lock.release()
        self.is_lock = False




class PAUSE_429_Extension:
    def __init__(self, crawler):
        print("Extension init...")
        self.crawler = crawler
        self.pause_time = crawler.settings.get("PAUSETIME_429", 20)
        self.lock_manager = LockManager()

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler)
        crawler.signals.connect(ext.handle_response, signal=signals.response_received)
        crawler.lock_manager = ext.lock_manager  # 共享锁
        return ext

    def handle_response(self, response, request, spider):
        if response.status == 429:
            ExtensionLog.info(f"请求url:{request.url}时遇到429错误，将暂停{self.pause_time}秒")
            self.lock_manager.acquire()
            time.sleep(self.pause_time)
            self.lock_manager.release()


