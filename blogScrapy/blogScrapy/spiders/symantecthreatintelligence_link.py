import scrapy
from scrapy.http import Request, Response
from tqdm import tqdm
from ..items import *
from scrapy import signals
from urllib.parse import urlencode
from uuid import uuid4
from lxml import html
import threading
import logging
import os
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast

# Comment 增加了链接去重功能

class Symantecthreatintelligencespider(scrapy.Spider):
    website_name = "symantecthreatintelligence"
    name = "symantecthreatintelligence_link"
    allowed_domains = ["www.security.com"]
    start_urls = []

    # 查询url
    query_base_url = "https://www.security.com/blogs/api/v1/blogs/search"

    # TODO 需要自己设置大概得文章篇数（至少要大于真实的文章篇数，温馨提示上一次总共爬到了315篇）
    article_num = 1000

    # 请求头Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Accept': '*/*'
    }

    # 用于记录获取多少链接
    link_num = 0

    # 进度条
    link_bar = None

    # 自制日志记录器
    myLog = logging.getLogger("Symantecthreatintelligence")

    def __init__(self, *args, **kwargs):
        super(Symantecthreatintelligencespider, self).__init__(*args, **kwargs)

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

        for i in range(0, int(self.article_num / 20) + 1):
            params = {
                'blog': 221,
                'rows': 20,
                'page': 20 * i
            }
            url = self.query_base_url + '?' + urlencode(params)
            yield Request(url=url,
                          headers=self.headers,
                          dont_filter=True,
                          callback=self.get_article_links,
                          errback=self.err_parse)
    def get_article_links(self, response):
        # 用于存储链接
        links = []

        # 获取查询结果json
        data = response.json()

        # 获取html对象
        results = data['results']

        # 文章链接的xpath的路径
        links.extend([result['postUrl'] for result in results])

        # 链接去重
        links = list(set(links))


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
            self.myLog.error(f"请求Url:{url}时出错次数超过最大重试次数！Retry num exceeded max!")
            return None

    def closed(self, reason):
        self.myLog.info(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
