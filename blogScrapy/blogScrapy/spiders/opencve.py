import scrapy
from scrapy.http import Request, Response
from typing import Any
from ..items import *
import base64
import json
import logging


class OpencveSpider(scrapy.Spider):
    website_name = "opencve"
    name = "opencve"
    allowed_domains = ["app.opencve.io"]
    start_urls = ["https://app.opencve.io/api/cve?page=1"]

    # 处理部分错误请求
    handle_httpstatus_list = [403]

    # 认证信息
    username = "evenking"
    password = "jyh1349458478"

    # 小批量调试限制
    limination = 10
    cnt = 0

    # page num（用于为爬取的数据分配文件名）
    page_num = 0

    headers = {
        "Authorization": f'Basic {base64.b64encode(f"{username}:{password}".encode()).decode()}'
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url,
                          dont_filter=True,
                          headers=self.headers,
                          callback=self.parse_cve_json)

    def parse_cve_json(self, response):

        if response.status == 403:
            print("Error Response:", response.text)
            return

        data = json.loads(response.text)
        self.page_num += 1

        # For debug
        self.cnt += 1
        if self.cnt <= self.limination:

            item = JsonItem()
            item['data'] = data
            item['filename'] = str(self.page_num) + '.json'

            yield item

            if 'next' in data:
                print(f"page_num:{self.page_num}完成，准备爬取下一页：{data['next']}")
                yield Request(data['next'],
                              dont_filter=True,
                              headers=self.headers,
                              callback=self.parse_cve_json)
            else:
                # logging.info(f"数据爬取结束，page num:{self.page_num}")
                print(f"数据爬取结束，page num:{self.page_num}")




