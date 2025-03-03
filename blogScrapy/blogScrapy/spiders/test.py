import scrapy
from scrapy.http import Request, Response
from tqdm import tqdm
from typing import Any
from ..items import *
import uuid
import threading

class TestSpider(scrapy.Spider):
    name = "test"
    start_urls = ["https://www.nccgroup.com//us/research-blog/tool-release-scoutsuite-5130/"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url,
                          callback=self.parse)
    def parse(self, response):
        print("text:", response.text)