import scrapy
from scrapy.http import Request, Response, JsonRequest
from selenium.webdriver.common.by import By
from tqdm import tqdm
from ..items import *
from scrapy import signals
from uuid import uuid4
import threading
import logging
import os
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast
import json
import copy

# Comment 增加了链接去重功能

class NccgroupLinkSpider(scrapy.Spider):
    website_name = "nccgroup"
    name = "nccgroup_link"
    allowed_domains = ["www.nccgroup.com"]

    start_urls = ['https://www.nccgroup.com/research/research-articles']
    api_url = "https://www.nccgroup.com/api/related/query?culture=en"

    domain_name = "https://www.nccgroup.com"

        # 请求体模板
    payload = {
        "ContentTypes": ["research"],
        "ResourceTypes": [],
        "Categories": [],
        "Sectors": [],
        "Services": [],
        "SortOrder": None,
        "RootNode": "16856",
        "Authors": [],
        "ExcludedIds": [],
        # "ExcludedIds": ["26228", "26226", "26219", "26224", "26210", "26192", "26178", "26106", "26104", "26089"],
        "ResultAmount": "9",
        "IsUserQuery": True,
        "CultureFallback": False
    }

    excluded_ids = ["26228", "26226", "26219", "26224", "26210", "26192", "26178", "26106", "26104", "26089"]

    # 请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': 'https://www.nccgroup.com',
        'Referer': 'https://www.nccgroup.com/research/research-articles/',
    }

    # 用于记录获取多少链接
    link_num = 0

    # 进度条
    link_bar = None

    # 自制日志记录器
    myLog = logging.getLogger("Nccgroup")

    def __init__(self, *args, **kwargs):
        super(NccgroupLinkSpider, self).__init__(*args, **kwargs)

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
                          callback=self.parse_home_page,
                          errback=self.err_parse,
                          meta={
                              'selenium_wait_by': By.XPATH,
                              'selenium_wait_target': '//div[@id="content-hub-items"]//a[@class="e-btn"]'
                          })
        # yield JsonRequest(
        #     url=self.api_url,
        #     headers=self.headers,
        #     cookies=self.extra_cookies,
        #     dont_filter=True,
        #     data=self.payload,
        #     callback=self.parse_article_json,
        #     errback=self.err_parse
        # )
            
    def parse_home_page(self, response):
        links = []

        page = response.meta.get("playwright_page")
        if page:
            page.close()

        self.payload['ExcludedIds'].extend(response.xpath(
            '//div[@id="content-hub-items"]/div/@data-id').getall())

        links.extend([self.domain_name + link for link in response.xpath('//div[@id="content-hub-items"]//a[@class="e-btn"]/@href').getall()])
        links = list(set(links))
        self.myLog.info(f"url:{response.request.url}共获取到{len(links)}个文章链接")

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
            yield linkItem

        yield JsonRequest(
            url=self.api_url,
            headers=self.headers,
            dont_filter=True,
            data=copy.deepcopy(self.payload),
            callback=self.parse_article_json,
            errback=self.err_parse,
            meta={"is_json": True}
        )
    
    def parse_article_json(self, response):
        
        data = response.json()
        
        old_ids_num = len(self.payload["ExcludedIds"])

        page_ids = [content['id'] for content in data['content']]
        self.payload["ExcludedIds"].extend(page_ids)
        
        links = [content['rssFeedUrl'] for content in data['content']]
        links = list(set(links))

        # 去重
        self.payload["ExcludedIds"] = list(set(self.payload["ExcludedIds"]))
        self.myLog.info(f"共获取到{len(links)}个文章链接")

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
            yield linkItem

        # 当ids集没有出现增量时停止爬取（即产生增量时才会继续爬取）
        if len(self.payload["ExcludedIds"])  > old_ids_num:
            self.myLog.info(f"ids集增加了{len(self.payload['ExcludedIds']) - old_ids_num}个，继续爬取")
            yield JsonRequest(
                url=self.api_url,
                headers=self.headers,
                dont_filter=True,
                data=copy.deepcopy(self.payload),
                callback=self.parse_article_json,
                errback=self.err_parse,
                meta={"is_json": True}
            )
        


    def err_parse(self, failure):
        response = getattr(failure.value, 'response', None)
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
            retry_request = request.copy()
            retry_request.meta['retry_cnt'] = retry_cnt + 1
            self.myLog.info(f"第{retry_cnt}次重试请求Url:{url}")
            return retry_request
        else:
            self.myLog.error(f"请求Url:{url}时出错次数超过最大重试次数！")
            return None

    def closed(self, reason):
        self.myLog.info(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
