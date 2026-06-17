# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
import requests
import logging
import time
import os

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


MiddleWareLog = logging.getLogger("MiddleWare")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
MiddleWareLog.addHandler(stream_handler)

class BlogscrapySpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class BlogscrapyDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

class SeleniumMiddleware(object):

    def __init__(self):
        MiddleWareLog.info("启用Selenium下载器")

        # 配置 ChromeOptions
        self.options = Options()
        self.options.add_argument('--headless=new')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.options.add_argument('--allow-insecure-localhost')
        self.options.add_argument('--disable-web-security')
        self.options.add_argument('--disable-gpu')  # 禁用 GPU，加速无头模式渲染
        self.options.add_argument('--disable-dev-shm-usage')  # 防止内存不足错误
        self.options.add_argument('--window-size=1920x1080')  # 指定窗口大小以避免页面渲染异常
        


    def process_request(self, request, spider):
        browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

        url = request.url

        try:
            browser.get(url)

            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))  # 修改为页面上需要的关键元素
            )

            html = browser.page_source
            return HtmlResponse(url=request.url,
                                body=html,
                                request=request,
                                encoding='utf-8',
                                status=200)
        except Exception as e:
            return HtmlResponse(status=403)

        finally:
            browser.quit()


class SeleniumImageDownloaderMiddleware:
    def __init__(self):
        # 初始化 Selenium WebDriver
        options = Options()
        # options.add_argument('--headless')
        options.add_argument('--ignore-certificate-errors')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--allow-insecure-localhost')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-gpu')  # 禁用 GPU，加速无头模式渲染
        options.add_argument('--disable-dev-shm-usage')  # 防止内存不足错误
        options.add_argument('--window-size=1920x1080')  # 指定窗口大小以避免页面渲染异常

        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        MiddleWareLog.info("Selenium Img Crawl Start...")

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_closed(self):
        # 关闭 WebDriver
        self.browser.quit()

    def process_request(self, request, spider):
        # 仅处理带 'selenium' meta 的请求
        # 用 Selenium 打开图片 URL
        self.browser.get(request.url)

        # 获取图片数据
        img_data = requests.get(request.url).content

        # 返回 Response，让 Scrapy 的 Image Pipeline 处理
        return HtmlResponse(url=request.url, body=img_data, encoding='utf-8', request=request)
