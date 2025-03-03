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


class LevelblueLinkSpider(scrapy.Spider):
    website_name = "levelblue"
    name = "levelblue_link"
    allowed_domains = ["levelblue.com"]
    start_urls = []

    # 用于和页数拼接
    page_base_url = "https://levelblue.com/blogs/security-essentials/"

    # 用于和文章链接拼接
    article_base_url = "https://levelblue.com"

    # 请求头Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        'Accept': 'application/json'
    }

    # 用于记录获取多少链接
    link_num = 0

    # TODO 请手动指定页面数量
    page_num = 177

    # 进度条
    link_bar = None

    # 自制日志记录器
    myLog = logging.getLogger("LevelBlueLog")

    def __init__(self, *args, **kwargs):
        super(LevelblueLinkSpider, self).__init__(*args, **kwargs)

        # 设置进度条
        self.link_bar = tqdm(total=self.page_num, desc='从导航页面获取文章链接', unit="page")

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

    # 直接构造各导航页的url
    def start_requests(self):
        yield Request(url=self.page_base_url,
                      headers=self.headers,
                      dont_filter=True,
                      callback=self.get_article_links,
                      errback=self.err_parse)

        for i in range(1, self.page_num):
            url = self.page_base_url + "P" + str(9 * i)
            yield Request(url=url,
                          headers=self.headers,
                          dont_filter=True,
                          callback=self.get_article_links,
                          errback=self.err_parse)

    def get_article_links(self, response):
        # 用于存储链接
        links = []

        # 文章链接的xpath的路径
        links.extend([self.article_base_url + href for href in response.xpath(
            '//div[@class="blog-card-cta"]/a/@href').getall()])

        self.link_bar.update(1)

        self.myLog.info(f"url:{response.request.url}共获取到{len(links)}个文章链接")
        self.link_num += len(links)

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
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
