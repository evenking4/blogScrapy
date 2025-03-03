import scrapy
from scrapy.http import Request, Response
from tqdm import tqdm
from ..items import *
from scrapy import signals
from uuid import uuid4
import threading
import logging
import os
from scrapy.exceptions import CloseSpider
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast

class HtmlCrawlSpider(scrapy.Spider):
    name = "bin_crawl"

    # 请求头Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Accept': '*/*'
    }

    myLog = logging.getLogger("myLog")

    all_links = {}

    # fumo~fumo~
    fumo_bar = None

    def __init__(self, target=None, *args, **kwargs):
        super(HtmlCrawlSpider, self).__init__(*args, **kwargs)
        self.target = target

        # 单target版本地兼容性措施，后续可能会改成多target
        self.website_name = target

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

    def statistics_links(self, all_links):
        for root, dirs, files in os.walk(f"./raw_html/{self.target}/", topdown=True):
            completed_keys = set(dirs)
            break
        uncompleted_links = {k: v for k, v in all_links.items() if k not in completed_keys}
        self.myLog.info(f"需要爬取的链接共有{len(all_links)}个，已完成爬取的共有{len(completed_keys)}个，还剩{len(uncompleted_links)}个链接需要爬取")
        return uncompleted_links

    # 确认返回的html内容正确(TODO)
    def detection_html(self, response):
        return True

    # 处理未爬取成功的请求。重爬，写入日志
    def handle_error(self, response, request):

        # 最大重试次数
        max_retry = 5

        url = request.url

        uuid = request.meta.get('uuid', None)
        if not uuid:
            self.myLog.fatal("未获取到文章的uuid，退出程序")
            raise CloseSpider("未获取到文章的uuid，退出程序")

        retry_cnt = request.meta.get('retry_cnt', 0)

        if retry_cnt <= max_retry:
            self.myLog.info(f"第{retry_cnt}次重试请求Url:{url}")
            return Request(url=url,
                           headers=self.headers,
                           dont_filter=True,
                           callback=self.handle_html,
                           meta={"uuid": uuid, "retry_cnt": retry_cnt + 1},
                           errback=self.err_parse)
        else:
            self.myLog.error(f"请求Url:{url}时出错次数超过最大重试次数！Retry num exceeded max!")
            return None



    def start_requests(self):
        if self.target:
            self.myLog.info(f"准备爬取目标网站:{self.target}")
        else:
            self.myLog.error(f"未指定目标网站")
            return

        link_file_path = f"links/{self.target}/{self.target}.txt"
        with open(link_file_path, "r", encoding='utf-8') as f:
            content = f.read()
            self.all_links = {line.split(' ')[0]: line.split(' ')[1] for line in content.split('\n') if line}

        uncompleted_links = self.statistics_links(self.all_links)

        self.fumo_bar = tqdm(total=len(uncompleted_links), desc='勤劳的Fumo正在工作 ᗜᴗᗜ ...', unit="page")

        for uuid, link in uncompleted_links.items():
            yield Request(url=link,
                          headers=self.headers,
                          dont_filter=True,
                          callback=self.handle_html,
                          meta={"uuid": uuid},
                          errback=self.err_parse)

    def handle_html(self, response, **kwargs):
        if not self.detection_html(response):
            # 移交给错误处理函数
            return self.handle_error(response)


        # update fumo bar
        self.fumo_bar.update(1)

        uuid = response.meta.get("uuid", None)

        if not uuid:
            self.myLog.fatal("未获取到文章的uuid，退出程序")
            raise CloseSpider("未获取到文章的uuid，退出程序")

        bin_item = BinItem()
        bin_item["uuid"] = uuid
        bin_item["url"] = response.request.url
        bin_item["website"] = self.target
        bin_item["filename"] = "raw.pdf"
        bin_item["data"] = response.body

        yield bin_item

    def err_parse(self, failure):
        request = failure.request
        response = getattr(failure.value, "response", None)
        if response:
            self.myLog.error(f"在请求URL:{request.url}时出现错误。状态码为{response.status}")
        else:
            self.myLog.error(f"在请求URL:{request.url}，且没有response")

        # 移交给错误处理函数
        return self.handle_error(response, request)

    def closed(self, reason):
        self.myLog.info(f"Spider:{self.name}结束，reason:{reason}")
        self.statistics_links(self.all_links)


