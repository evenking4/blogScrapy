import scrapy
from scrapy.http import Request, Response
from tqdm import tqdm
from ..items import *
from scrapy import signals
import uuid
import threading
import logging
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast


class CloudflareLinkSpider(scrapy.Spider):
    website_name = "cloudflare"
    name = "cloudflare_link"
    allowed_domains = ["blog.cloudflare.com"]
    start_urls = ["https://blog.cloudflare.com/tag/security/"]

    # 用于和页数拼接
    page_base_url = "https://blog.cloudflare.com/tag/security/page/"

    # 用于和文章href拼接
    article_base_url = "https://blog.cloudflare.com"

    # 用于记录获取多少链接
    link_num = 0

    # 进度条
    link_bar = None

    # 自制日志记录器
    myLog = logging.getLogger("myLog")

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, dont_filter=True, callback=self.get_page_num, errback=self.err_parse)

    # 从首页获取站点的全局信息，如有多少页数。
    def get_page_num(self, response):

        # 用于存储链接
        links = []

        # page_num xpath路径
        page_num = int(response.xpath('//ul[@class="flex list ml3"]/li[last()]/a/text()').get())

        # 小批量调试
        # page_num = 2

        # 设置进度条
        self.link_bar = tqdm(total=page_num, desc='从导航页面获取文章链接', unit="page")

        if page_num:
            self.myLog.info(f"获取{self.website_name}主页成功，共有{page_num}页目录页")
        else:
            self.myLog.error(f"从主页获取页数失败")
            return

        # 文章链接的xpath路径
        links.extend([self.article_base_url + href for href in response.xpath(
            '//a[@data-testid="post-title"]/@href | //article[@data-testid="more-posts-article"]/a/@href').getall()])

        self.myLog.info(f"首页共获取到{len(links)}个文章链接")
        self.link_num += len(links)

        self.link_bar.update(1)

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid.uuid4().hex
            linkItem['url'] = link
            yield linkItem

        # 从其他导航页获取文章链接
        for i in range(2, page_num + 1):
            url = self.page_base_url + str(i)
            yield Request(url=url, dont_filter=True, callback=self.get_article_links, errback=self.err_parse)

    def get_article_links(self, response):
        # 用于存储链接
        links = []

        # 文章链接的xpath的路径
        links.extend([self.article_base_url + href for href in response.xpath(
            '//a[@data-testid="post-title"]/@href | //article[@data-testid="more-posts-article"]/a/@href').getall()])

        self.link_bar.update(1)

        self.myLog.info(f"url:{response.request.url}共获取到{len(links)}个文章链接")
        self.link_num += len(links)

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid.uuid4().hex
            linkItem['url'] = link
            yield linkItem

    def err_parse(self, failure):
        response = failure.value.response
        if response:
            self.myLog.error(f"在请求URL:{response.request.url}时出现错误。状态码为{response.status}")
        else:
            self.myLog.error("无响应")

    def closed(self, reason):
        # self.myLog.info(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
        print(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
