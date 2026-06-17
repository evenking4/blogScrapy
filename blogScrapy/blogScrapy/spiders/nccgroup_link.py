import scrapy
from scrapy.http import Request, Response, HtmlResponse
from ..items import *
from scrapy import signals
from uuid import uuid4
import logging
import os
import subprocess
import json
import time


class NccgroupLinkSpider(scrapy.Spider):
    website_name = "nccgroup"
    name = "nccgroup_link"
    allowed_domains = ["www.nccgroup.com"]
    start_urls = ["https://www.nccgroup.com/research/research-articles/"]

    # API 端点
    api_url = "https://www.nccgroup.com/api/related/query?culture=en"

    # 请求体模板
    api_body_template = {
        "ContentTypes": ["research"],
        "ResourceTypes": [],
        "Categories": [],
        "Sectors": [],
        "Services": [],
        "SortOrder": None,
        "RootNode": "16856",
        "Authors": [],
        "ExcludedIds": [],
        "ResultAmount": "9",
        "IsUserQuery": True,
        "CultureFallback": False
    }

    # 请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': 'https://www.nccgroup.com',
        'Referer': 'https://www.nccgroup.com/research/research-articles/',
    }

    link_num = 0
    myLog = logging.getLogger("NccgroupLog")

    def __init__(self, waf_token=None, *args, **kwargs):
        super(NccgroupLinkSpider, self).__init__(*args, **kwargs)
        # 可选的 Azure WAF token（从浏览器获取）
        self.waf_token = waf_token

        os.makedirs(f'log/{self.name}', exist_ok=True)
        file_handler = logging.FileHandler(f'log/{self.name}/log.txt', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.myLog.addHandler(file_handler)
        self.myLog.addHandler(stream_handler)
        self.myLog.debug("###################Start###################")

    def _call_api(self, excluded_ids):
        """调用 API 获取新文章，返回 (articles, all_ids)"""
        body = dict(self.api_body_template)
        body["ExcludedIds"] = excluded_ids

        body_json = json.dumps(body)
        curl_cmd = [
            'curl', '-s', '--max-time', '30',
            '-H', f'User-Agent: {self.headers["User-Agent"]}',
            '-H', f'Accept: {self.headers["Accept"]}',
            '-H', f'Content-Type: {self.headers["Content-Type"]}',
            '-H', f'Origin: {self.headers["Origin"]}',
            '-H', f'Referer: {self.headers["Referer"]}',
            '-d', body_json,
            self.api_url
        ]

        # 如果有 WAF token，添加 cookie
        if self.waf_token:
            curl_cmd.insert(5, '-H')
            curl_cmd.insert(6, f'Cookie: {self.waf_token}')

        for attempt in range(3):
            try:
                result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=35)
                if result.returncode == 0 and result.stdout:
                    data = json.loads(result.stdout)
                    return self._parse_response(data)
                else:
                    self.myLog.warning(f"API 调用失败，返回码 {result.returncode}，第{attempt+1}次重试")
                    time.sleep(5)
            except json.JSONDecodeError:
                body_preview = result.stdout[:200] if result.stdout else ''
                self.myLog.warning(f"API 返回非 JSON 数据: {body_preview}")
                if 'Azure WAF' in (result.stdout or '') or 'azwaf' in (result.stdout or ''):
                    self.myLog.error("检测到 Azure WAF JS Challenge，需要浏览器获取有效 cookie")
                    return [], []
                time.sleep(5)
            except Exception as e:
                self.myLog.warning(f"curl 调用异常: {e}，第{attempt+1}次重试")
                time.sleep(5)

        return [], []

    def _parse_response(self, data):
        """解析 API 响应，返回 (articles, all_ids)"""
        articles = []
        all_ids = []

        # 尝试多种可能的响应结构
        results = None
        if isinstance(data, dict):
            results = data.get('results') or data.get('data') or data.get('items') or data.get('Resources')

        if results and isinstance(results, list):
            for item in results:
                article_id = str(item.get('Id') or item.get('id') or item.get('Key') or '')
                url = item.get('Url') or item.get('url') or item.get('Link') or ''
                if article_id:
                    all_ids.append(article_id)
                if url:
                    # 确保完整 URL
                    if url.startswith('/'):
                        url = 'https://www.nccgroup.com' + url
                    articles.append(url)

        # 打印原始 keys 以便调试
        if isinstance(data, dict) and not results:
            self.myLog.info(f"API 响应 keys: {list(data.keys())[:10]}")

        return articles, all_ids

    def start_requests(self):
        """启动爬取流程"""
        if not self.waf_token:
            self.myLog.warning("=" * 60)
            self.myLog.warning("未提供 waf_token 参数！")
            self.myLog.warning("该网站使用 Azure WAF JS Challenge 保护，")
            self.myLog.warning("需要从浏览器获取有效的 cookie 后传入。")
            self.myLog.warning("用法: scrapy crawl nccgroup_link -a waf_token='cookie_value'")
            self.myLog.warning("=" * 60)

        self.myLog.info("开始爬取 NCC Group 研究文章...")

        all_articles = set()
        excluded_ids = []

        # 循环调用 API 直到没有新文章返回
        page = 1
        while True:
            self.myLog.info(f"第 {page} 次 API 调用，已排除 {len(excluded_ids)} 个 ID")
            articles, new_ids = self._call_api(excluded_ids)

            if not articles:
                self.myLog.info(f"API 未返回新文章，爬取完成")
                break

            # 去重
            new_articles = [a for a in articles if a not in all_articles]
            all_articles.update(articles)

            self.myLog.info(f"获取到 {len(articles)} 篇文章（新增 {len(new_articles)} 篇）")
            self.link_num += len(new_articles)

            for link in new_articles:
                linkItem = LinkItem()
                linkItem['uuid'] = uuid4().hex
                linkItem['url'] = link
                yield linkItem

            # 更新排除列表
            excluded_ids.extend(new_ids)
            page += 1

            # 安全上限
            if page > 200:
                self.myLog.warning("达到最大页数限制 (200)，停止")
                break

            # 请求间隔
            time.sleep(2)

        self.myLog.info(f"爬取完成，共获取 {len(all_articles)} 篇去重文章")

    def closed(self, reason):
        self.myLog.info(f"Spider:{self.name}爬取完成，共获取到链接{self.link_num}个")
