import scrapy
from scrapy.http import Request, Response, HtmlResponse
from tqdm import tqdm
from ..items import *
from scrapy import signals
from uuid import uuid4
import threading
import logging
import os
import re
import subprocess
import time
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast


class Mcafeespider(scrapy.Spider):
    website_name = "mcafee"
    name = "mcafee_link"
    allowed_domains = ["www.mcafee.com"]
    start_urls = ["https://www.mcafee.com/blogs/mobile-security/",
                  "https://www.mcafee.com/blogs/internet-security/",
                  "https://www.mcafee.com/blogs/privacy-identity-protection/"]

    # 请求头Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    # 用于记录获取多少链接
    link_num = 0

    # 自制日志记录器
    myLog = logging.getLogger("Mcafee")

    def __init__(self, *args, **kwargs):
        super(Mcafeespider, self).__init__(*args, **kwargs)

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

    # def _fetch(self, url, retry=3):
    #     """使用 curl 命令发起请求以绕过 Akamai TLS 指纹检测"""
    #     for attempt in range(retry):
    #         try:
    #             result = subprocess.run([
    #                 'curl', '-sL', '--compressed', '--max-time', '30',
    #                 '-H', f'User-Agent: {self.headers["User-Agent"]}',
    #                 '-H', f'Accept: {self.headers["Accept"]}',
    #                 '-H', f'Accept-Language: {self.headers["Accept-Language"]}',
    #                 url
    #             ], capture_output=True, text=True, timeout=35)
    #             if result.returncode == 0 and result.stdout:
    #                 # 请求间较长延迟，避免触发 Akamai 速率限制
    #                 time.sleep(8)
    #                 return HtmlResponse(url=url, status=200,
    #                                    body=result.stdout.encode('utf-8'), encoding='utf-8')
    #             else:
    #                 self.myLog.warning(f"curl 返回码 {result.returncode}，第{attempt+1}次重试")
    #                 time.sleep(10)
    #         except Exception as e:
    #             self.myLog.warning(f"curl 调用异常: {e}，第{attempt+1}次重试")
    #             time.sleep(10)
    #     self.myLog.error(f"请求 {url} 在 {retry} 次重试后仍失败")
    #     return HtmlResponse(url=url, status=500, body=b'')

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url,
                          headers=self.headers,
                          dont_filter=True,
                          callback=self.get_page_num,
                          cb_kwargs={
                              "page_url": url,
                          },
                          errback=self.err_parse)

        # 从首页获取站点的全局信息，如有多少页数。
    def get_page_num(self, response, page_url):
        # 用于存储链接
        links = []

        # page_num xpath路径
        page_num = int(response.xpath('(//li/a[@class="page-numbers"])[last()]/text()').get())

        print("page_num:", page_num)

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

        links.extend(response.xpath(
            '//div[@class="card"]//div[@class="card-image-topic"]/a/@href').getall())

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
            url = page_url + 'page/' + str(i)
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
            '//div[@class="card"]//div[@class="card-image-topic"]/a/@href').getall())

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
