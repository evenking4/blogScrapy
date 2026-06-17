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

class Paloaltospider(scrapy.Spider):
    website_name = "paloalto"
    name = "paloalto_link"
    allowed_domains = ["www.paloaltonetworks.com"]
    # 占位
    start_urls = ["https://www.mcafee.com/blogs/mobile-security/",
                  "https://www.mcafee.com/blogs/internet-security/",
                  "https://www.mcafee.com/blogs/privacy-identity-protection/"]

    catalog = ["post",              # Corporate Blogs 3792
               "net_sec_post",      # Network Security Blogs 277
               "sase_post",         # SASE Blogs 292
               "cloud_sec_post",    # Cloud Native Security Blogs 428
               "sec_ops_post"]      # Security Operations Blogs 460

    # 查询url
    query_base_url = "http://www.paloaltonetworks.com/blog/wp-admin/admin-ajax.php"

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
    myLog = logging.getLogger("Paloalto")

    def __init__(self, *args, **kwargs):
        super(Paloaltospider, self).__init__(*args, **kwargs)

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
        for ptype in self.catalog:
            params = {
                'action': 'posts_infinite',
                'data[ptype]': ptype,
                'data[lang]': 'en',
                'data[search]': 'false',
                'data[offset]': '0',
                'data[featuredPostId]': '',
                'data[type]': 'strata'
            }
            url = self.query_base_url + '?' + urlencode(params)
            yield Request(url=url,
                          headers=self.headers,
                          dont_filter=True,
                          cb_kwargs={'ptype': ptype},
                          callback=self.get_page_num,
                          errback=self.err_parse)

    # 从首页获取站点的全局信息，如有多少页数。
    def get_page_num(self, response, **kwargs):

        # 用于存储链接
        links = []

        # 查询类型
        ptype = kwargs['ptype']

        # 获取查询结果json
        data = response.json()

        # 获取html对象
        html_text = data['html']
        html_obj = html.fromstring(html_text)

        # 计算文章数量和页数
        article_num = data['offset'] + data['rem_posts']
        page_num = int((article_num - 1) / 8 + 1)

        # 小批量调试
        # page_num = 5

        if page_num:
            self.myLog.info(f"获取{self.website_name}主页成功，共有{page_num}页目录页")
        else:
            self.myLog.error(f"从主页获取页数失败")
            return

        # 文章链接的xpath路径
        links.extend(html_obj.xpath(
            '//h2[@class="title"]/a/@href'))

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
        for i in range(1, page_num):
            params = {
                'action': 'posts_infinite',
                'data[ptype]': ptype,
                'data[lang]': 'en',
                'data[search]': 'false',
                'data[offset]': 8 * i,
                'data[featuredPostId]': '',
                'data[type]': 'strata'
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
        html_text = data['html']
        html_obj = html.fromstring(html_text)

        # 文章链接的xpath的路径
        links.extend(html_obj.xpath(
            '//h2[@class="title"]/a/@href'))

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
