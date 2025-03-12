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

class KasperskyThreatSpider(scrapy.Spider):
    website_name = "kaspersky_threat"
    name = "kaspersky_threat_link"
    allowed_domains = ["threats.kaspersky.com"]
    start_urls = ["https://threats.kaspersky.com/en/threat/"]

    # 用于和页数拼接
    page_base_url = "https://threats.kaspersky.com/en/threat/?paged="

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
    myLog = logging.getLogger("KasperskyThreat")

    def __init__(self, *args, **kwargs):
        super(KasperskyThreatSpider, self).__init__(*args, **kwargs)

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
        page_num = int(response.xpath('//div[@class="pagination__list"]/div[last()-1]/text()').get())

        print("page_num:", page_num)

        # 限制爬取数量
        page_num = 70

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
        links.extend(response.xpath(
            '//div[@class="table"]/div[@class="table__row"]/div[1]/a/@href').getall())

        # 链接去重
        links = list(set(links))

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
        links.extend(response.xpath(
            '//div[@class="table"]/div[@class="table__row"]/div[1]/a/@href').getall())

        links = list(set(links))

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
        request = failure.request
        print(response.text)
        if response:
            self.myLog.error(f"在请求URL:{request.url}时出现错误。状态码为{response.status}")
        else:
            self.myLog.error(f"在请求URL:{request.url}，且没有response")

        # 移交给错误处理函数
        return self.handle_error(response, request)

    # 处理未爬取成功的请求。重爬，写入日志
    def handle_error(self, response, request):

        # 最大重试次数
        max_retry = 5

        url = request.url

        retry_cnt = request.meta.get('retry_cnt', 0)

        if retry_cnt <= max_retry:
            self.myLog.info(f"第{retry_cnt}次重试请求Url:{url}")
            return Request(url=url,
                           headers=self.headers,
                           dont_filter=True,
                           callback=request.callback,
                           meta={"retry_cnt": retry_cnt + 1},
                           errback=self.err_parse)
        else:
            self.myLog.error(f"请求Url:{url}时出错次数超过最大重试次数！")
            return None

    def closed(self, reason):
        self.myLog.info(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
