import scrapy
from scrapy.http import Request, Response
from tqdm import tqdm
from ..items import *
from scrapy import signals
from uuid import uuid4
import threading
import logging
import os
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast

# Comment 增加了链接去重功能

class TrendmicroSpider(scrapy.Spider):
    website_name = "trendmicro"
    name = "trendmicro_link"
    allowed_domains = ["www.trendmicro.com"]

    # 请求头Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Accept': 'application/json'
    }

    base_url = 'https://www.trendmicro.com/en_us/research.tagSearch.json'

    # 用于记录获取多少链接
    link_num = 0

    # 进度条
    link_bar = None

    # 自制日志记录器
    myLog = logging.getLogger("Trendmicro")

    def __init__(self, *args, **kwargs):
        super(TrendmicroSpider, self).__init__(*args, **kwargs)

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

    def cat_params(self, params):
        return '&'.join(['tags=' + param for param in params])

    def start_requests(self):
        base_url = 'https://www.trendmicro.com/en_us/research.tagSearch.json'

        threats_category = [
            'trend-micro-research:threats/apt-and-targeted-attacks',
            'trend-micro-research:threats/artificial-intelligence-ai',
            'trend-micro-research:threats/compliance-and-risks',
            'trend-micro-research:threats/cyber-crime',
            'trend-micro-research:threats/cyber-threats',
            'trend-micro-research:threats/deep-web',
            'trend-micro-research:threats/exploits-and-vulnerabilities',
            'trend-micro-research:threats/malware',
            'trend-micro-research:threats/phishing',
            'trend-micro-research:threats/privacy-and-risks',
            'trend-micro-research:threats/ransomware',
            'trend-micro-research:threats/spam',
            'trend-micro-research:threats/risk-management',
        ]

        environments_category = [
            'trend-micro-research:environments/asrm',
            'trend-micro-research:environments/cloud',
            'trend-micro-research:environments/connected-car',
            'trend-micro-research:environments/data-center',
            'trend-micro-research:environments/endpoints',
            'trend-micro-research:environments/ics-ot',
            'trend-micro-research:environments/iot',
            'trend-micro-research:environments/mobile',
            'trend-micro-research:environments/network',
            'trend-micro-research:environments/smart-home',
            'trend-micro-research:environments/social-media',
            'trend-micro-research:environments/tm-vision-one-platform',
            'trend-micro-research:environments/web',
        ]

        medium_category = [
            'trend-micro-research:medium/article',
            'trend-micro-research:medium/infographic',
            'trend-micro-research:medium/broadcast',
            'trend-micro-research:medium/podcast',
            'trend-micro-research:medium/report',
            'trend-micro-research:medium/video',
            'trend-micro-research:medium/webinar'
        ]

        article_type_category = [
            'trend-micro-research:article-type/letstalk-series',
            'trend-micro-research:article-type/annual-predictions',
            'trend-micro-research:article-type/consumer-focus',
            'trend-micro-research:article-type/expert-perspective',
            'trend-micro-research:article-type/foresight-predictive',
            'trend-micro-research:article-type/technical',
            'trend-micro-research:article-type/investigations',
            'trend-micro-research:article-type/latest-news',
            'trend-micro-research:article-type/reports',
            'trend-micro-research:article-type/research',
            'trend-micro-research:article-type/security-strategies',
        ]

        yield Request(url=self.base_url,
                        headers=self.headers,
                        dont_filter=True,
                        callback=self.get_article_links,
                        cb_kwargs={'param_list': [], 'tags_list': [article_type_category, medium_category, threats_category, environments_category]},
                        errback=self.err_parse)

        # url_pools = []

        # for i1 in threats_category:
        #     for i2 in environments_category:
        #         for i3 in article_type_category:
        #             for i4 in medium_category:
        #                 url_pools.append(base_url + '?' + self.cat_params([i1, i2, i3, i4]))

        # for i in threats_category:
        #     url_pools.append(base_url + '?' + self.cat_params([i]))

        # for i in environments_category:
        #     url_pools.append(base_url + '?' + self.cat_params([i]))

        # for i in article_type_category:
        #     url_pools.append(base_url + '?' + self.cat_params([i]))

        # for i in medium_category:
        #     url_pools.append(base_url + '?' + self.cat_params([i]))

        # # 设置进度条
        # self.link_bar = tqdm(total=len(url_pools), desc='fumo勤劳工作中 ᗜˬᗜ...', unit="page")

        # for url in url_pools:
        #     yield Request(url=url,
        #                   headers=self.headers,
        #                   dont_filter=True,
        #                   callback=self.get_article_links,
        #                   errback=self.err_parse)


    def get_article_links(self, response, param_list=[], tags_list=[]):
        # 用于存储链接
        links = []

        data = response.json()

        links = [article['path'] for article in data['articles']]
        links_num = len(links)
        links = list(set(links))

        self.link_num += len(links)

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
            yield linkItem

        # 这个狗屎网站的API每次最多返回100条数据
        # 这个标签返回的条数到100了，就需要用更细致的标签组合去获取连接
        self.myLog.info(f"标签组合{param_list}共获取到{len(links)}个文章链接")
        if links_num >= 100 and len(tags_list) > 0:
            self.myLog.info(f"标签组合{param_list}进入更深一步组合")
            new_tags_list = tags_list[1:]
            tags_pool = tags_list[0]
            for tag in tags_pool:
                new_param_list = param_list + [tag]
                new_url = self.base_url + '?' + self.cat_params(new_param_list)
                yield Request(url=new_url,
                              headers=self.headers,
                              dont_filter=True,
                              callback=self.get_article_links,
                              cb_kwargs={'param_list': new_param_list, 'tags_list': new_tags_list},
                              errback=self.err_parse)
                
            


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
