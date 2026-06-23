import scrapy
from scrapy.http import Request, Response
from tqdm import tqdm
from ..items import *
from scrapy import signals
from uuid import uuid4
import threading
import logging
import os
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast
from parsel import Selector

# Comment TODO 注意：无法直接运行
# Comment 由于目标网站将所有链接放在单页网页当中且需要滑动加载
# Comment 方便起见，我直接将加载完毕的网页保存下来进行解析
# Comment 保存地址为temp/fsecure.html（可能已经删除）

class FsecureSpider(scrapy.Spider):
    website_name = "fsecure"
    name = "fsecure_link"
    start_urls = []


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
    myLog = logging.getLogger("Fsecure")

    def __init__(self, *args, **kwargs):
        super(FsecureSpider, self).__init__(*args, **kwargs)

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

    #fake Request
    def start_requests(self):
        yield Request(url="https://www.baidu.com",
                      headers=self.headers,
                      callback=self.test)

    def test(self, response):
        with open(f"temp/fsecure.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        sele = Selector(text=html_content)

        links =  sele.xpath('//article[@class="sc-1d81036b-1 iRiOvi sc-f14be06e-0 fmodni"]/a/@href').getall()

        self.link_num += len(links)

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
            yield linkItem


    def closed(self, reason):
        self.myLog.info(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
