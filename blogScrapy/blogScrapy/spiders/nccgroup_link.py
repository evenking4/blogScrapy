import scrapy
from scrapy.http import Request, Response, JsonRequest
from tqdm import tqdm
from ..items import *
from scrapy import signals
from uuid import uuid4
import threading
import logging
import os
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast
import json

# Comment 增加了链接去重功能

class NccgroupLinkSpider(scrapy.Spider):
    website_name = "nccgroup"
    name = "nccgroup_link"
    allowed_domains = ["www.nccgroup.com"]

    start_urls = ['https://www.nccgroup.com/research/research-articles/?afd_azwaf_tok=eyJraWQiOiIxNkY3M0JFMkNDMjZDOUM1ODBGMzM4NjAzN0I1ODRCQTc4REQ1ODcwQUFFRkJGNEZDRUJFOUZEQkNGMENGMTNEIiwiYWxnIjoiUlMyNTYifQ.eyJhdWQiOiJ3d3cubmNjZ3JvdXAuY29tIiwiZXhwIjoxNzgyMjE2OTkyLCJpYXQiOjE3ODIyMTY5ODIsImlzcyI6InRpZXIxLTVjZjg3ZDY3YzgtaGJuOWYiLCJzdWIiOiIyMDYuMjM3LjExOS4yMzUiLCJkYXRhIjp7InR5cGUiOiJpc3N1ZWQiLCJyZWYiOiIyMDI2MDYyM1QxMjE2MjJaLTE1Y2Y4N2Q2N2M4aGJuOWZoQzFISzFuZWhnMDAwMDAwMDQ1ZzAwMDAwMDAwa3YzMiIsImIiOiI2clFZUnNlTGlmdW44b05EeFFBUFhyLUlRdXlGRFY3UjljQ20xY055dF9vIiwiaCI6IklLdXJIeXVScjB3dllPLTRMSUdrNWR6TDRRZE03NDhtYzdoSE52bll4ZG8ifX0.I7363lbA-JuRWyh8HYmy1nhUtSM_X6FHNaWLR4UV9iWWM2wWEhGOOTPws0a3Fr9Q2aw-6CGyvWyjFfwJ35nki5UxeuWELsyR1DeVP3BSFGzZhzYG4IVh6K29LCZizrhSumTtCwlrcmaiQ59Qgqa1tKlxm5KIgX5pJuRn6DQFYslGuuFV-EIQ8fqmCHp5BUDahjVN36FDknLzZ1YgvlbD36l7tNHED6bENeSFidzjlDT5crfS8nk4CGGIJzGjGCarZ6_y_ZW4h_nBUPZUGps_njenKaBQ1Bg7bweRjlnhw4c63Alg7TP1rcp2l__lewGsCxm9iaxDQSIa1weQA8tEJw.WF3obl2IDtqgvMFRqVdYkD5s']

    api_url = "https://www.nccgroup.com/api/related/query?culture=en"

    domain_name = "https://www.nccgroup.com"

        # 请求体模板
    payload = {
        "ContentTypes": ["research"],
        "ResourceTypes": [],
        "Categories": [],
        "Sectors": [],
        "Services": [],
        "SortOrder": None,
        "RootNode": "16856",
        "Authors": [],
        # "ExcludedIds": [],
        "ExcludedIds": ["26228", "26226", "26219", "26224", "26210", "26192", "26178", "26106", "26104", "26089"],
        "ResultAmount": "9",
        "IsUserQuery": True,
        "CultureFallback": False
    }

    # excluded_ids = []

    excluded_ids = ["26228", "26226", "26219", "26224", "26210", "26192", "26178", "26106", "26104", "26089"]

    # 请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': 'https://www.nccgroup.com',
        'Referer': 'https://www.nccgroup.com/research/research-articles/',
    }

    extra_cookies = {
        'afd_azwaf_jsclearance': 'afd_azwaf_jsclearance=eyJraWQiOiIxNkY3M0JFMkNDMjZDOUM1ODBGMzM4NjAzN0I1ODRCQTc4REQ1ODcwQUFFRkJGNEZDRUJFOUZEQkNGMENGMTNEIiwiYWxnIjoiUlMyNTYifQ.eyJhdWQiOiJ3d3cubmNjZ3JvdXAuY29tIiwiZXhwIjoxNzgyMjE4Nzg1LCJpYXQiOjE3ODIyMTY5ODUsImlzcyI6InRpZXIxLTVjZjg3ZDY3YzgtendydmsiLCJzdWIiOiIyMDYuMjM3LjExOS4yMzUiLCJkYXRhIjp7InR5cGUiOiJwYXNzIiwicmVmIjoiMjAyNjA2MjNUMTIxNjI1Wi0xNWNmODdkNjdjOHp3cnZraEMxSEsxcGZ4YzAwMDAwMDAzYjAwMDAwMDAwMDZ2NzUifX0.RYLB_zD4QRJ-Gx2-cLu-9hkbPsnVAc9bt8ml-Bv1_X9s7JIixbGtDoviN6gTgQJSTnSjYp6CunUMC6sG-25Qgw4pip2--NJiS6hWkiniQHeZQ9PCrzSxkRV8xwdJXnnxmFl_4zR_1UmVuByEC3l_GECvCkiPOZSDIXJ8n9jtJ0yRPI2VBvge-bLJ5eQpl0V3wFN6f38Rgi2ZsyV9-enyleZhVZR1IILMGuRJpZ-UXcAlefWjXfdH11Yy5j8Qpiaus51mjoGVuD6yDh5mjPba1uIn0xXHQTAGCdgfnP0P3qjA2aCMzfOd0Ni99H6bZMSOEOpQYFnVVsmBeXGOW3ACDw'
    }

    # 用于记录获取多少链接
    link_num = 0

    # 进度条
    link_bar = None

    # 自制日志记录器
    myLog = logging.getLogger("Nccgroup")

    def __init__(self, *args, **kwargs):
        super(NccgroupLinkSpider, self).__init__(*args, **kwargs)

        # 设置日志输出
        os.makedirs(f'log/{self.name}', exist_ok=True)
        file_handler = logging.FileHandler(f'log/{self.name}/log.txt', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        self.myLog.addHandler(file_handler)
        self.myLog.addHandler(stream_handler)

        # self.headers['Cookie'] = 'CookieControl=%7B%22necessaryCookies%22%3A%5B%221P_JAR%22%2C%22ARRAffinity%22%2C%22XSRF-TOKEN%22%2C%22XSRF-V%22%2C%22CookieControl%22%2C%22APISID%22%2C%22GPS%22%2C%22HSID%22%2C%22IDE%22%2C%22SAPISID%22%2C%22SID%22%2C%22SSID%22%2C%22__Secure-3PAPISID%22%2C%22__Secure-3PSID%22%2C%22__Secure-APISID%22%2C%22__Secure-HSID%22%2C%22__Secure-SSID%22%2C%22NID%22%2C%22SIDCC%22%2C%22test_cookie%22%2C%22VISITOR_INFO1_LIVE%22%2C%22YSD%22%2C%22YSC%22%2C%22player%22%2C%22UMB-*%22%2C%22UMB_*%22%2C%22Language%22%2C%22ASP.NET_SessionId%22%2C%22__RequestVerificationToken%22%2C%22__cfduid%22%2C%22bcookie%22%2C%22_uv_id%22%2C%22ncc_lang%22%2C%22ncc_country%22%5D%2C%22optionalCookies%22%3A%7B%22analytics%22%3A%22accepted%22%2C%22marketing%22%3A%22accepted%22%7D%2C%22statement%22%3A%7B%22shown%22%3Atrue%2C%22updated%22%3A%2228%2F02%2F2024%22%7D%2C%22consentDate%22%3A1781445183172%2C%22consentExpiry%22%3A90%2C%22interactedWith%22%3Atrue%2C%22user%22%3A%22F102F62C-DFC3-4583-90C9-5807570532A9%22%7D; intercom-id-nncj4mdb=05d099c4-5861-49b1-ad40-c5f940f25462; intercom-session-nncj4mdb=; umbracoEngageAnalyticsVisitorId=CfDJ8PgbG9wkzhtAl2oMaV7TE6s1EqIwypGZppL5HMVBg%2Bwzq7ozK8xq1zxhIsBFFah5NpkX5GKgW7ZRLqqhfCIXMPk0HGaIzkxvxCtLiXFdhDT8UNJTblo3AOqUMi5STruUF8ip7IQ2Mvs%2BwyfyQXjpZCu9W8sDMG44bgUNlKiydKMd; _gid=GA1.2.1070863258.1782199753; .AspNetCore.Antiforgery.7BGImYovB8M=CfDJ8PgbG9wkzhtAl2oMaV7TE6t4R6fd2gKAwFHFpWS-Gj7vKREuz1Z6si2XFTH5j41tZTyMKIq7kmBLe85ZclgK9FvomT-CMG4fmIva6b7C3m5YowHnOPbijXkSipYZ2wC9qMlLXIdwf83cG9pBLghP79A; ARRAffinity=e62b947e6340589f02236fa9ca24cbc0ba3f5749107df36ea12aae4b8106c265; ARRAffinitySameSite=e62b947e6340589f02236fa9ca24cbc0ba3f5749107df36ea12aae4b8106c265; ASLBSA=00032522bb33d622013cfbb790da6a8cb15dd559db919103380cc1d6338178a38969; ASLBSACORS=00032522bb33d622013cfbb790da6a8cb15dd559db919103380cc1d6338178a38969; afd_azwaf_jsclearance=eyJraWQiOiIxNkY3M0JFMkNDMjZDOUM1ODBGMzM4NjAzN0I1ODRCQTc4REQ1ODcwQUFFRkJGNEZDRUJFOUZEQkNGMENGMTNEIiwiYWxnIjoiUlMyNTYifQ.eyJhdWQiOiJ3d3cubmNjZ3JvdXAuY29tIiwiZXhwIjoxNzgyMjE2MzAxLCJpYXQiOjE3ODIyMTQ1MDEsImlzcyI6InRpZXIxLTU1Yzc4YzhjZjctemQyZHciLCJzdWIiOiIyMDYuMjM3LjExOS4yMzUiLCJkYXRhIjp7InR5cGUiOiJwYXNzIiwicmVmIjoiMjAyNjA2MjNUMTEzNTAxWi0xNTVjNzhjOGNmN3pkMmR3aEMxSEtHcWFnMDAwMDAwMDA0YzAwMDAwMDAwMDJoOHoifX0.COm7odnHF2KykX3REKZ_5_7Siz6s_585nL3i045kfhQb4-dcQ7sxjqmi-N-z3weg47UcK7T_KSg2yeJGLHY_NT6nH6hkc20hyead0Jq48-PMqlTl_hjKU4xxnYJQRxrjd7Jf_kcDKoGhM5-fkMffp6aE6V1S3nJO2FJ3mujQweT4Dmkxr51_SUSvrmY-T8jKxFpXCbJjOktte6HbWwUxaZZbPsq1I-bP4QZHbMxWE3se2xm2oBdPxVUCfmWg6f9BzCx2pUkiptyc19HvoWGoDnGyLNsfhSdJDS3LlmfOMVNap1euGMXphExwF0PelcWU9JP2YJi4pLSPGPhLSPcrYQ; .AspNetCore.Mvc.CookieTempDataProvider=CfDJ8PgbG9wkzhtAl2oMaV7TE6s1zcBJcToUV1YJEm5pTaFvtXp4pDUrMBmMK0cyz-lNMEL1SOA-L6Xa8td0DXuHqtjErI_MrLfU6Q4fw2ysH7qNl7hJ5zQfyXpZwsjK6kkJuDDYTPIj2o97t2BCAOzvUyXIxadfjpzSaAeFjBNufSsEd8GGwBwuQ8HXjpUWpho8lvOmESSadf9_114wDo9lSBQ; _gcl_au=1.1.739544667.1782214533; _ga_5CFJL7SCLR=GS2.1.s1782214533$o1$g0$t1782214533$j60$l0$h0; _ga=GA1.2.191222830.1781445184; _clck=1kevotc%5E2%5Eg75%5E0%5E2365; visitor_id898251=652116481; visitor_id898251-hash=584b896d66751e1865ad7894dd4af4d9c99635abd980546143b16ab77c0d4753134e2dd57e28a286af3eaf4957a63473c9c71160; _clsk=b546cx%5E1782214534517%5E1%5E1%5Ef.clarity.ms%2Fcollect; _zitok=c96ce9ff272dec3d960f1782214534'

        # 日志起点
        self.myLog.debug("###################Start###################")

    def start_requests(self):
        # for url in self.start_urls:
        #     yield Request(url=url,
        #                   headers=self.headers,
        #                   dont_filter=True,
        #                   callback=self.parse_home_page,
        #                   errback=self.err_parse)
        yield JsonRequest(
            url=self.api_url,
            headers=self.headers,
            cookies=self.extra_cookies,
            dont_filter=True,
            data=self.payload,
            callback=self.parse_article_json,
            errback=self.err_parse
        )
            
    def parse_home_page(self, response):
        links = []

        page = response.meta.get("playwright_page")
        if page:
            page.close()

        self.excluded_ids.extend(response.xpath(
            '//div[@id="content-hub-items"]/div/@data-id').getall())

        links.extend([self.domain_name + link for link in response.xpath('//div[@id="content-hub-items"]//a[@class="e-btn"]/@href').getall()])
        links = list(set(links))
        self.myLog.info(f"url:{response.request.url}共获取到{len(links)}个文章链接")

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
            yield linkItem

        # payload = self.api_body_template.copy()
        # payload['ExcludedIds'] = self.excluded_ids
        payload = {}

        yield JsonRequest(
            url=self.api_url,
            headers=self.headers,
            cookies=self.extra_cookies,
            dont_filter=True,
            data=payload,
            callback=self.parse_article_json,
            errback=self.err_parse
        )
    
    def parse_article_json(self, response):
        
        data = response.json()
        
        old_ids_num = len(self.payload["ExcludedIds"])

        page_ids = [content['id'] for content in data['content']]
        self.payload["ExcludedIds"].extend(page_ids)
        
        links = [content['rssFeedUrl'] for content in data['content']]
        links = list(set(links))

        # 去重
        self.payload["ExcludedIds"] = list(set(self.payload["ExcludedIds"].copy()))
        self.myLog.info(f"共获取到{len(links)}个文章链接")

        for link in links:
            linkItem = LinkItem()
            linkItem['uuid'] = uuid4().hex
            linkItem['url'] = link
            yield linkItem

        # 当ids集没有出现增量时停止爬取（即产生增量时才会继续爬取）
        if len(self.payload["ExcludedIds"])  > old_ids_num:
            yield JsonRequest(
                url=self.api_url,
                headers=self.headers,
                dont_filter=True,
                data=self.payload,
                callback=self.parse_article_json,
                errback=self.err_parse
            )
        


    def err_parse(self, failure):
        response = getattr(failure.value, 'response', None)
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
