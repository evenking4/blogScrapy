import scrapy
from scrapy.http import Request, Response
from tqdm import tqdm
from ..items import *
from bs4 import BeautifulSoup
from scrapy import signals
from uuid import uuid4
import threading
import logging
import json
import os
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast

# Comment 增加了链接去重功能

class AptnotesSpider(scrapy.Spider):
    website_name = "aptnotes"
    name = "aptnotes_link"
    start_urls = ["https://raw.githubusercontent.com/aptnotes/data/master/APTnotes.json"]

    # # 用于和文章链接拼接
    # article_base_url = "https://www.crowdstrike.com"


    # 请求头Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Accept': 'application/json'
    }

    # 用于记录获取多少链接
    link_num = 0

    # 进度条
    link_bar = None

    # 自制日志记录器
    myLog = logging.getLogger("Aptnotes")

    def __init__(self, *args, **kwargs):
        super(AptnotesSpider, self).__init__(*args, **kwargs)

        # 设置日志输出
        os.makedirs(f'log/{self.name}', exist_ok=True)
        file_handler = logging.FileHandler(f'log/{self.name}/log.txt', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        self.myLog.addHandler(file_handler)
        self.myLog.addHandler(stream_handler)

        # 日志起点
        self.myLog.debug("###################Start###################")

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url,
                          headers=self.headers,
                          dont_filter=True,
                          callback=self.get_page_links,
                          errback=self.err_parse)

    def get_page_links(self, response):
        # 用于存储链接
        page_links = []

        data = response.json()

        page_links = [article['Link'] for article in data]

        # 小批量调试
        # page_links = page_links[0: 1]

        for page_link in page_links:
            yield Request(url=page_link,
                          headers=self.headers,
                          dont_filter=True,
                          callback=self.get_article_links,
                          errback=self.err_parse)

    def get_article_links(self, response):
        page = response.text
        soup = BeautifulSoup(page, 'lxml')
        scripts = soup.find('body').find_all('script')
        sections = scripts[-1].contents
        sections = scripts[-1].contents[0].split(';')
        app_api = json.loads(sections[0].split('=')[1])['/app-api/enduserapp/shared-item']
        # Build download URL
        box_url = "https://app.box.com/index.php"
        box_args = "?rm=box_download_shared_file&shared_name={}&file_id={}"
        file_url = box_url + box_args.format(app_api['sharedName'], 'f_{}'.format(app_api['itemID']))
        linkItem = LinkItem()
        linkItem['uuid'] = uuid4().hex
        linkItem['url'] = file_url
        self.link_num += 1
        yield linkItem



    def err_parse(self, failure):
        response = failure.value.response
        print(response.text)
        if response:
            self.myLog.error(f"在请求URL:{response.request.url}时出现错误。状态码为{response.status}")
        else:
            self.myLog.error("无响应")

    def closed(self, reason):
        self.myLog.info(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
