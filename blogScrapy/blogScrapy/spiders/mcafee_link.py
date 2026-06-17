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

    def _fetch(self, url, retry=3):
        """使用 curl 命令发起请求以绕过 Akamai TLS 指纹检测"""
        for attempt in range(retry):
            try:
                result = subprocess.run([
                    'curl', '-sL', '--compressed', '--max-time', '30',
                    '-H', f'User-Agent: {self.headers["User-Agent"]}',
                    '-H', f'Accept: {self.headers["Accept"]}',
                    '-H', f'Accept-Language: {self.headers["Accept-Language"]}',
                    url
                ], capture_output=True, text=True, timeout=35)
                if result.returncode == 0 and result.stdout:
                    # 请求间较长延迟，避免触发 Akamai 速率限制
                    time.sleep(8)
                    return HtmlResponse(url=url, status=200,
                                       body=result.stdout.encode('utf-8'), encoding='utf-8')
                else:
                    self.myLog.warning(f"curl 返回码 {result.returncode}，第{attempt+1}次重试")
                    time.sleep(10)
            except Exception as e:
                self.myLog.warning(f"curl 调用异常: {e}，第{attempt+1}次重试")
                time.sleep(10)
        self.myLog.error(f"请求 {url} 在 {retry} 次重试后仍失败")
        return HtmlResponse(url=url, status=500, body=b'')

    def start_requests(self):
        for url in self.start_urls:
            response = self._fetch(url)
            if response.status != 200:
                self.myLog.error(f"请求 {url} 失败，状态码: {response.status}")
                continue

            self.myLog.info(f"成功获取分类首页: {url}")

            # 处理第一页，获取文章链接和总页数
            yield from self._process_first_page(response)

    def _process_first_page(self, response):
        """处理分类首页：提取总页数和第一页文章链接，然后爬取剩余页面"""
        url = response.url

        # 获取总页数
        page_nums = response.xpath(
            '//a[contains(@class, "page-numbers") and not(contains(@class, "next")) '
            'and not(contains(@class, "prev")) and not(contains(@class, "dots"))]/text()'
        ).getall()
        page_ints = [int(p) for p in page_nums if p.isdigit()]
        page_num = max(page_ints) if page_ints else 1

        self.myLog.info(f"分类 {url} 共 {page_num} 页")

        # 提取第一页文章链接
        links = self._extract_links(response)
        self.myLog.info(f"第1页共获取到{len(links)}个文章链接")
        self.link_num += len(links)

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
            yield linkItem

        # 请求剩余页面
        page_base_url = url.rstrip('/') + "/page/"
        for i in range(2, page_num + 1):
            page_url = page_base_url + str(i) + "/"
            page_response = self._fetch(page_url)
            if page_response.status != 200:
                self.myLog.error(f"请求 {page_url} 失败，跳过")
                continue

            links = self._extract_links(page_response)
            self.myLog.info(f"第{i}页共获取到{len(links)}个文章链接")
            self.link_num += len(links)

            for link in links:
                linkItem = LinkItem()
                linkItem['uuid'] = uuid4().hex
                linkItem['url'] = link
                yield linkItem

    def _extract_links(self, response):
        """从页面提取文章链接并去重"""
        links = response.xpath(
            '//*[contains(@class, "card-title")]/a/@href').getall()
        return list(set(links))

    def closed(self, reason):
        self.myLog.info(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
