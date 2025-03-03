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

class NvdcveSpider(scrapy.Spider):
    website_name = "nvdcve"
    name = "nvdcve_link"
    allowed_domains = ["services.nvd.nist.gov"]
    start_urls = ["https://services.nvd.nist.gov/rest/json/cves/2.0"]

    # 请求头Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Accept': 'application/json'
    }

    # 用于记录获取多少链接
    link_num = 0

    base_url = 'https://services.nvd.nist.gov/rest/json/cves/2.0?startIndex='

    # 进度条
    link_bar = None

    # 自制日志记录器
    myLog = logging.getLogger("Nvdcve")

    def __init__(self, *args, **kwargs):
        super(NvdcveSpider, self).__init__(*args, **kwargs)

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

        data = response.json()

        totalResults = int(data['totalResults'])

        page_num = int((totalResults - 1) / 2000)

        if not page_num:
            self.myLog.error(f"从主页获取页数失败")
            return


        self.myLog.info(f"首页共获取到{len(links)}个文章链接")
        self.link_num += len(links)

        for i in range(0, page_num + 1):
            linkItem = LinkItem()
            linkItem['uuid'] = str(i)
            linkItem['url'] = self.base_url + str(2000 * i)
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
