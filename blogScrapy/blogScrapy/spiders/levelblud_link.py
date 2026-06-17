import scrapy
from scrapy.http import Request, Response
from tqdm import tqdm
from ..items import *
from scrapy import signals
from uuid import uuid4
import threading
import logging
import os
import re
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast


class LevelblueLinkSpider(scrapy.Spider):
    website_name = "levelblue"
    name = "levelblue_link"
    allowed_domains = ["www.levelblue.com", "levelblue.com"]
    start_urls = ["https://www.levelblue.com/blogs/levelblue-blog"]

    blog_base_url = "https://www.levelblue.com/blogs/levelblue-blog"

    # 请求头Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    # 用于记录获取多少链接
    link_num = 0

    # 进度条
    link_bar = None

    # 自制日志记录器
    myLog = logging.getLogger("LevelBlueLog")

    def __init__(self, *args, **kwargs):
        super(LevelblueLinkSpider, self).__init__(*args, **kwargs)

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
        yield Request(url=self.blog_base_url,
                      headers=self.headers,
                      dont_filter=True,
                      callback=self.parse_first_page,
                      errback=self.err_parse)

    def parse_first_page(self, response):
        # 从第一页获取文章链接
        links = self._extract_links(response)

        # 获取总页数
        last_page = self._get_last_page(response)
        if not last_page:
            self.myLog.error("未能获取总页数，仅爬取首页")
            last_page = 1

        self.myLog.info(f"共检测到{last_page}页博客目录")

        # 设置进度条
        self.link_bar = tqdm(total=last_page, desc='从导航页面获取文章链接', unit="page")
        self.link_bar.update(1)

        self.myLog.info(f"第1页共获取到{len(links)}个文章链接")
        self.link_num += len(links)

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
            yield linkItem

        # 请求剩余页面
        for i in range(2, last_page + 1):
            yield Request(url=f"{self.blog_base_url}/page/{i}",
                          headers=self.headers,
                          dont_filter=True,
                          callback=self.parse_page,
                          errback=self.err_parse)

    def parse_page(self, response):
        links = self._extract_links(response)

        self.link_bar.update(1)

        self.myLog.info(f"url:{response.request.url}共获取到{len(links)}个文章链接")
        self.link_num += len(links)

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
            yield linkItem

    def _extract_links(self, response):
        """从页面提取文章链接"""
        links = response.xpath(
            '//a[contains(@class, "tw-link-block")]/@href').getall()
        return list(set(links))

    def _get_last_page(self, response):
        """从分页区域获取总页数"""
        last_page_url = response.xpath(
            '//a[contains(@class, "hs-pagination__link--last")]/@href').get()
        if last_page_url:
            match = re.search(r'/page/(\d+)', last_page_url)
            if match:
                return int(match.group(1))

        # 备选方案：从所有页码链接中取最大值
        page_nums = response.xpath(
            '//a[contains(@class, "hs-pagination__link--number")]/text()').getall()
        page_ints = [int(p) for p in page_nums if p.isdigit()]
        if page_ints:
            return max(page_ints)

        return None

    def err_parse(self, failure):
        response = failure.value.response
        request = failure.request
        if response:
            self.myLog.error(f"在请求URL:{request.url}时出现错误。状态码为{response.status}")
        else:
            self.myLog.error(f"在请求URL:{request.url}时出现错误，且没有response")

    def closed(self, reason):
        self.myLog.info(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
