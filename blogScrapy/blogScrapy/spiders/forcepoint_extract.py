import scrapy
from scrapy.http import Request, Response
from bs4 import BeautifulSoup
import html2text
import hashlib
from tqdm import tqdm
from ..items import *
from lxml import etree
from scrapy import signals
from uuid import uuid4
import threading
import logging
import os
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast

# Comment 增加了链接去重功能

class ForcePointExtracter(scrapy.Spider):
    website_name = "forcepoint"
    name = "forcepoint_extract"
    domain = "https://www.forcepoint.com"
    start_urls = []

    # 请求头Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Accept': 'application/json'
    }

    err_blog_num = 0

    # 进度条
    link_bar = None

    # 自制日志记录器
    myLog = logging.getLogger("Forcepoint")

    # 生成字符串对应的哈希值
    def hash_string(self, text, algorithm="sha256"):
        # 计算字符串的哈希值
        hash_func = hashlib.new(algorithm)  # 创建哈希对象
        hash_func.update(text.encode('utf-8'))  # 更新哈希对象
        return hash_func.hexdigest()  # 返回16进制摘要

    def is_absolute_url(self, url: str):
        return url.startswith(('http://', 'https://', 'www'))

    def __init__(self, *args, **kwargs):
        super(ForcePointExtracter, self).__init__(*args, **kwargs)

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
        all_uuids = set()

        for root, dirs, files in os.walk(f'./raw_html/{self.website_name}'):
            all_uuids = set(dirs)
            break

        # 设置进度条
        self.link_bar = tqdm(total=len(all_uuids), desc='fumo勤劳工作中 ᗜˬᗜ...', unit="page")

        for uuid in all_uuids:
            with open(f'raw_html/{self.website_name}/{uuid}/raw.html', "r", encoding="utf-8") as f:
                html_content = f.read()

            # 解析
            dom = etree.HTML(html_content)
            soup = BeautifulSoup(html_content, "html.parser")

            title = dom.xpath('//h1/text()')[0]
            # print('title:', title)

            tags = dom.xpath('//ul[@class="flex flex-wrap gap-3 md:justify-end"]/li/a/text()')
            # print('tags:', tags)

            main_soup = soup.find(name="div",
                                  class_="relative flex flex-col-reverse md:flex-row md:items-start md:gap-lg xl:gap-xl mx-auto max-w-screen-lg")

            if not main_soup:
                self.err_blog_num += 1
                print(f"未获取到{uuid}的文章主元素")
                continue

            # # 下载对应图片
            # for img in main_soup.find_all(name='img'):
            #     img_item = ImgItem()
            #     img_item['image_urls'] = img["src"] if self.is_absolute_url(img["src"]) else self.domain + img["src"]
            #     img_item['dir'] = f'main_content/{self.website_name}/{uuid}/img/'
            #     img_item['filename'] = self.hash_string(img_item['image_urls']) + '.jpg'
            #     os.makedirs(f'main_content/{self.website_name}/{uuid}/img/', exist_ok=True)
            #     yield img_item
            #
            #     img['src'] = 'img/' + img_item['filename']
            #     img['alt'] = img_item['image_urls']

            # 配置html2text处理器
            main_extracter = html2text.HTML2Text()
            main_extracter.body_width = 0

            text_content = main_extracter.handle(str(main_soup))

            output_dir = f'main_content/{self.website_name}/{uuid}/'
            os.makedirs(output_dir, exist_ok=True)
            with open(output_dir + 'content.md', 'w', encoding='utf-8') as f:
                f.write(text_content)

            # dict_item = DictItem()
            # dict_item['dir'] = f'main_content/{self.website_name}/{uuid}/'
            # dict_item['filename'] = 'info.json'
            # dict_item['data'] = {
            #     'title': title,
            #     'tags': tags,
            #     'text': text_content
            # }
            # yield dict_item

            self.link_bar.update(1)


    def err_parse(self, failure):
        response = failure.value.response
        print(response.text)
        if response:
            self.myLog.error(f"在请求URL:{response.request.url}时出现错误。状态码为{response.status}")
        else:
            self.myLog.error("无响应")

    def closed(self, reason):
        self.myLog.info(f"共有{self.err_blog_num}个博客在匹配正文时出现问题")
