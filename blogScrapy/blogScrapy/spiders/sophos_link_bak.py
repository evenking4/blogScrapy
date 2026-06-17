# import scrapy
# from scrapy.http import Request, Response
# from tqdm import tqdm
# from ..items import *
# from scrapy import signals
# from uuid import uuid4
# import threading
# import logging
# import os
# from twisted.internet.defer import Deferred
# from typing import TYPE_CHECKING, Any, cast

# # Comment 针对未指定最大页数的博客网站
# # Comment 通过开辟多个并行的请求链
# # Comment 既实现了自动确认了页数也利用异步请求提高了效率


# class Sophosspider(scrapy.Spider):
#     website_name = "sophos"
#     name = "sophos_link"
#     allowed_domains = ["news.sophos.com"]
#     start_urls = ["https://news.sophos.com/en-us/"]

#     # 请求头Headers
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
#         'Accept': 'application/json'
#     }

#     # 任务链数量
#     interval_num = 10

#     # 用于记录获取多少链接
#     link_num = 0

#     # 进度条
#     link_bar = None

#     # 自制日志记录器
#     myLog = logging.getLogger("Sophos")

#     def __init__(self, *args, **kwargs):
#         super(Sophosspider, self).__init__(*args, **kwargs)

#         # 设置日志输出
#         os.makedirs(f'log/{self.name}', exist_ok=True)
#         file_handler = logging.FileHandler(f'log/{self.name}/log.txt', encoding='utf-8')
#         file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#         stream_handler = logging.StreamHandler()
#         stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

#         self.myLog.addHandler(file_handler)
#         self.myLog.addHandler(stream_handler)

#         # 日志起点
#         self.myLog.debug("###################Start###################")

#     def start_requests(self):
#         for url in self.start_urls:
#             for page_num in range(1, self.interval_num + 1):
#                 yield Request(url=url + 'page/' + str(page_num),
#                               headers=self.headers,
#                               dont_filter=True,
#                               cb_kwargs={'page_base_url': url + 'page/', 'page_num': page_num},
#                               callback=self.get_article_links,
#                               errback=self.err_parse)

#     def get_article_links(self, response, **kwargs):
#         page_num = kwargs['page_num']

#         page_base_url = kwargs['page_base_url']

#         # 用于存储链接
#         links = []

#         # 文章链接的xpath的路径
#         links.extend(response.xpath(
#             '//a[@rel="bookmark"]/@href').getall())

#         # 链接去重
#         links = list(set(links))

#         self.myLog.info(f"url:{response.request.url}共获取到{len(links)}个文章链接")
#         self.link_num += len(links)

#         for link in links:
#             linkItem = LinkItem()
#             linkItem['uuid'] = uuid4().hex
#             linkItem['url'] = link
#             yield linkItem

#         # 以一定间隔爬取下个导航页
#         yield Request(url=page_base_url + str(page_num + 10),
#                       headers=self.headers,
#                       dont_filter=True,
#                       cb_kwargs={'page_base_url': page_base_url, 'page_num': page_num + 10},
#                       callback=self.get_article_links,
#                       errback=self.err_parse)

#     def err_parse(self, failure):
#         response = failure.value.response
#         request = failure.request
#         if response:
#             self.myLog.error(f"在请求URL:{request.url}时出现错误。状态码为{response.status}")
#         else:
#             self.myLog.error(f"在请求URL:{request.url}，且没有response")

#         if response.status == 404:
#             return None
#         else:
#             # 移交给错误处理函数
#             return self.handle_error(response, request)

#     # 处理未爬取成功的请求。重爬，写入日志
#     def handle_error(self, response, request):

#         # 最大重试次数
#         max_retry = 5

#         url = request.url

#         retry_cnt = request.meta.get('retry_cnt', 0)

#         if retry_cnt <= max_retry:
#             self.myLog.info(f"第{retry_cnt}次重试请求Url:{url}")
#             return Request(url=url,
#                            headers=self.headers,
#                            dont_filter=True,
#                            callback=request.callback,
#                            meta={"retry_cnt": retry_cnt + 1},
#                            errback=self.err_parse)
#         else:
#             self.myLog.error(f"请求Url:{url}时出错次数超过最大重试次数！Retry num exceeded max!")
#             return None

#     def closed(self, reason):
#         self.myLog.info(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
