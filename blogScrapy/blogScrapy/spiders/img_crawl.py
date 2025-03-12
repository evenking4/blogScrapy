import scrapy
from scrapy.http import Request, Response
from tqdm import tqdm
from ..items import *
from scrapy import signals
from uuid import uuid4
import threading
import logging
import json
import os
from scrapy.exceptions import CloseSpider
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast

class ImgCrawlSpider(scrapy.Spider):
    name = "img_crawl"

    # 请求头Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Accept': '*/*'
    }

    myLog = logging.getLogger("imgLog")

    all_links = {}

    # fumo~fumo~
    fumo_bar = None

    def __init__(self, *args, **kwargs):
        super(ImgCrawlSpider, self).__init__(*args, **kwargs)
        self.target = kwargs.get('target', None)

        # 单target版本地兼容性措施，后续可能会改成多target
        self.website_name = kwargs.get('target', None)

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

    def get_target_img_items(self):
        all_image_num = 0

        image_items = []

        blog_ids = set()

        os.makedirs(f'main_content/{self.website_name}', exist_ok=True)
        for root, dirs, files in os.walk(f'main_content/{self.website_name}', topdown=True):
            blog_ids = set(dirs)
            break

        for uuid in blog_ids:
            try:
                with open(f'main_content/{self.website_name}/{uuid}/img_infos.json') as f:
                    infos = json.load(f)
                    for info in infos:
                        all_image_num += 1

                        # 跳过爬取成功的图片
                        if os.path.exists(info['dir'] + info['filename']):
                            continue

                        image_item = ImgItem()
                        image_item['dir'] = info['dir']
                        image_item['filename'] = info['filename']
                        image_item['image_urls'] = info['image_urls']
                        image_item['appendix'] = {
                            'uuid': uuid
                        },
                        image_item['retry_cnt'] = 0
                        image_items.append(image_item)
            except Exception as e:
                print(f"读取{uuid}图片信息时出现错误{str(e)}")

        self.myLog.info(f'总共有图片{all_image_num}张,已爬取{all_image_num - len(image_items)}张，还剩{len(image_items)}张未爬，完成率为{((all_image_num - len(image_items)) / all_image_num) * 100}%')

        return image_items


    def start_requests(self):
        if self.target:
            self.myLog.info(f"准备爬取目标网站:{self.target}")
        else:
            self.myLog.error(f"未指定目标网站")
            return

        image_items = self.get_target_img_items()

        self.fumo_bar = tqdm(total=len(image_items), desc='勤劳的Fumo正在工作 ᗜᴗᗜ ...', unit="page")

        for image_item in image_items:
            yield image_item
            self.fumo_bar.update(1)

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


