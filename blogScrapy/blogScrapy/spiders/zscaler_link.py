import scrapy
from scrapy.http import Request, Response, JsonRequest
from selenium.webdriver.common.by import By
from tqdm import tqdm
from ..items import *
from scrapy import signals
from uuid import uuid4
import threading
import logging
import json
import copy
import os
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast

# Comment 增加了链接去重功能
# https://www.zscaler.com/blogs?current=n_3_n&size=n_8_n&filters%5B0%5D%5Bfield%5D=blog_category.keyword&filters%5B0%5D%5Bvalues%5D%5B0%5D=Security%20Research&filters%5B0%5D%5Btype%5D=any&sort%5B0%5D%5Bfield%5D=created&sort%5B0%5D%5Bdirection%5D=desc

# TODO 设置页数
page_num = 389

class ZsclaerSpider(scrapy.Spider):
    website_name = "zscaler"
    name = "zscaler_link"
    allowed_domains = ["www.zscaler.com"]
    start_urls = ["https://www.zscaler.com/blogs?size=n_8_n&filters%5B0%5D%5Bfield%5D=blog_category.keyword&filters%5B0%5D%5Bvalues%5D%5B0%5D=Security%20Research&filters%5B0%5D%5Btype%5D=any&sort%5B0%5D%5Bfield%5D=created&sort%5B0%5D%5Bdirection%5D=desc"]

    api_url = "https://www.zscaler.com/api/search"

    # 请求头Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Content-Type': 'application/json',
        'Origin': 'https://www.zscaler.com',
        'Referer': 'https://www.zscaler.com/blogs',
    }

    # 用于记录获取多少链接
    link_num = 0

    # 进度条
    link_bar = None

    # 自制日志记录器
    myLog = logging.getLogger("Rsa")

    def __init__(self, *args, **kwargs):
        super(ZsclaerSpider, self).__init__(*args, **kwargs)

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
        self.link_bar = tqdm(total=page_num, desc='fumo勤劳工作中 ᗜˬᗜ...', unit="page")
        with open("payloads/zscaler.json", "r", encoding="utf-8") as f:
            payload_template = json.load(f)
        for i in range(1, page_num + 1):
            payload = copy.deepcopy(payload_template)
            payload['requestState']['current'] = i
            yield JsonRequest(url=self.api_url,
                              headers=self.headers,
                              data=payload,
                              dont_filter=True,
                              callback=self.get_article_links,
                              errback=self.err_parse)

    def get_article_links(self, response):
        # 用于存储链接
        links = []
        # self.logger.debug(f"状态码: {response.status}, 返回内容: {response.text[:500]}")
        data = response.json()

        # 文章链接的xpath的路径
        links.extend(["https://www.zscaler.com" + article["_source"]["url"][0] for article in data["rawResponse"]["hits"]["hits"]])


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


    # def get_article_links(self, response):
    #     # 用于存储链接
    #     links = []
    #
    #     # 文章链接的xpath的路径
    #     links.extend(response.xpath(
    #         '//a[@class="text-pink !no-underline after:absolute after:inset-0"]').getall())
    #
    #
    #     links = list(set(links))
    #
    #     self.link_bar.update(1)
    #
    #     self.myLog.info(f"url:{response.request.url}共获取到{len(links)}个文章链接")
    #     self.link_num += len(links)
    #
    #     for link in links:
    #         linkItem = LinkItem()
    #         linkItem['uuid'] = uuid4().hex
    #         linkItem['url'] = link
    #         yield linkItem
    #
    # def err_parse(self, failure):
    #     response = failure.value.response
    #     request = failure.request
    #     print(response.text)
    #     if response:
    #         self.myLog.error(f"在请求URL:{request.url}时出现错误。状态码为{response.status}")
    #     else:
    #         self.myLog.error(f"在请求URL:{request.url}，且没有response")
    #
    #     # 移交给错误处理函数
    #     return self.handle_error(response, request)

    # 处理未爬取成功的请求。重爬，写入日志
    def handle_error(self, response, request):

        # 最大重试次数
        max_retry = 5

        url = request.url

        retry_cnt = request.meta.get('retry_cnt', 0)

        if retry_cnt <= max_retry:
            self.myLog.info(f"第{retry_cnt}次重试请求Url:{url}")
            retry_request = request.copy()
            retry_request.meta['retry_cnt'] = retry_cnt + 1
            return retry_request
        else:
            self.myLog.error(f"请求Url:{url}时出错次数超过最大重试次数！")
            return None

    def closed(self, reason):
        self.myLog.info(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
