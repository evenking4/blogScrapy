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

class ThehackernewsSpider(scrapy.Spider):
    website_name = "thehackernews"
    name = "thehackernews_link"
    allowed_domains = ["thehackernews.com"]
    start_urls = ["https://thehackernews.com/search/label/data%20breach",
                  "https://thehackernews.com/search/label/Cyber%20Attack",
                  "https://thehackernews.com/search/label/Vulnerability"]

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
    myLog = logging.getLogger("Thehackernews")

    def __init__(self, *args, **kwargs):
        super(ThehackernewsSpider, self).__init__(*args, **kwargs)

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
                          cb_kwargs={"page_num": 1},
                          callback=self.get_article_links,
                          errback=self.err_parse)

    def get_article_links(self, response, **kwargs):

        page_num = kwargs['page_num']

        # 用于存储链接
        links = []

        # 文章链接的xpath的路径
        links.extend(response.xpath(
            '//div[@class="body-post clear"]/a/@href').getall())

        links = list(set(links))

        self.myLog.info(f"url:{response.request.url}的第{page_num}页中共获取到{len(links)}个文章链接")
        self.link_num += len(links)

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
            yield linkItem

        next_link = response.xpath(
            '//span[@id="blog-pager-older-link"]/a/@href').get()

        if next_link:
            yield Request(url=next_link,
                          headers=self.headers,
                          dont_filter=True,
                          cb_kwargs={"page_num": page_num + 1},
                          callback=self.get_article_links,
                          errback=self.err_parse)
        else:
            self.myLog.info(f"url:{response.request.url}中没有下一页链接，获取完成")



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
