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

# Comment 增加了链接去重功能

class ForcepointSpider(scrapy.Spider):
    website_name = "forcepoint"
    name = "forcepoint_link"
    allowed_domains = ["www.forcepoint.com"]
    start_urls = ["https://www.forcepoint.com/blog/"]

    # 用于和页数拼接
    page_base_url = "https://www.forcepoint.com/blog?page="

    # 用于和文章链接拼接
    article_base_url = "https://www.forcepoint.com/"


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
    myLog = logging.getLogger("Forcepoint")

    def __init__(self, *args, **kwargs):
        super(ForcepointSpider, self).__init__(*args, **kwargs)

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
                          callback=self.get_page_num,
                          errback=self.err_parse)

    # 从首页获取站点的全局信息，如有多少页数。
    def get_page_num(self, response):

        # 用于存储链接
        links = []

        
        # page_num xpath路径
        page_num = int(response.xpath('//*[@id="main-content"]//ul[@class="flex items-center"]//li[@class="items-center text-h4 font-semibold mx-auto flex-shrink-0"]/text()').get().split("of")[-1].strip())


        # 小批量调试
        # page_num = 5

        # 设置进度条
        self.link_bar = tqdm(total=page_num, desc='fumo勤劳工作中 ᗜˬᗜ...', unit="page")

        if page_num:

            # 更新进度条
            self.link_bar.update(1)

            self.myLog.info(f"获取{self.website_name}主页成功，共有{page_num}页目录页")
        else:
            self.myLog.error(f"从主页获取页数失败")
            return

        # 文章链接的xpath路径
        links.extend([self.article_base_url + href for href in set(response.xpath(
            '//a[starts-with(@href, "/blog/x-labs/") or starts-with(@href, "/blog/insights/")]/@href').getall())])

        self.myLog.info(f"首页共获取到{len(links)}个文章链接")
        self.link_num += len(links)

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
            yield linkItem

        # 从其他导航页获取文章链接
        for i in range(2, page_num + 1):
            url = self.page_base_url + str(i)
            yield Request(url=url,
                          headers=self.headers,
                          dont_filter=True,
                          callback=self.get_article_links,
                          errback=self.err_parse)

    def get_article_links(self, response):
        # 用于存储链接
        links = []

        # 文章链接的xpath的路径
        links.extend([self.article_base_url + href for href in set(response.xpath(
            '//a[starts-with(@href, "/blog/x-labs/") or starts-with(@href, "/blog/insights/")]/@href').getall())])

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
