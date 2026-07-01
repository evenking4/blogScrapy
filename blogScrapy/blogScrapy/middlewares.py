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
        MiddleWareLog.info("启用全局持久化 Selenium 下载器")

        # 1. 配置 ChromeOptions
        self.options = Options()
        # 开启无头模式
        # self.options.add_argument('--headless=new')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        self.options.add_argument('--allow-insecure-localhost')
        self.options.add_argument('--disable-web-security')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--window-size=1920x1080')

        # 禁止加载图片提高爬取速率
        # prefs = {
        #     "profile.managed_default_content_settings.images": 2
        # }
        # self.options.add_experimental_option("prefs", prefs)

        # # 核心策略 2：通过 Blink 渲染引擎参数禁用图片（双重保险）
        # self.options.add_argument('--blink-settings=imagesEnabled=false')

        # 2. 【核心改动】在初始化时，整个爬虫生命周期只拉起“这一个”浏览器进程
        self.browser = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.options
        )

    @classmethod
    def from_crawler(cls, crawler):
        # 3. 注册 Scrapy 信号：当爬虫关闭时，自动释放并关闭浏览器进程
        middleware = cls()
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def process_request(self, request, spider):
        url = request.url

        wait_by = request.meta.get("selenium_wait_by", By.CSS_SELECTOR)
        wait_target = request.meta.get("selenium_wait_target", "body")
        wait_time = request.meta.get("selenium_wait_time", 30)

        print("wait_target:", wait_target)

        try:
            # 4. 【核心改动】每个请求不新开浏览器，而是利用 JS 在当前浏览器里新开一个独立的标签页（Tab）
            self.browser.execute_script(f'window.open("{url}");')

            # 5. 将控制权切换到最新打开的这个标签页
            self.browser.switch_to.window(self.browser.window_handles[-1])
            current_handle = self.browser.current_window_handle

            # 6. 等待目标元素加载
            # WebDriverWait(self.browser, 30).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            # )
            WebDriverWait(self.browser, wait_time).until(
                EC.presence_of_element_located((wait_by, wait_target))
            )

            html = self.browser.page_source

            # 7. 拿到数据后，立刻关闭当前标签页，防止标签页堆积导致内存爆炸
            self.browser.close()

            # 8. 如果浏览器还有剩余标签，把控制权交还给第一个页签（防止 Selenium 迷失焦点）
            if self.browser.window_handles:
                self.browser.switch_to.window(self.browser.window_handles[0])

            return HtmlResponse(url=url,
                                body=html,
                                request=request,
                                encoding='utf-8',
                                status=200)

        except Exception as e:
            # 异常时也要确保关闭刚才打开的标签页
            MiddleWareLog.info(f"浏览器出现异常 {e}")
            try:
                if len(self.browser.window_handles) > 1:
                    self.browser.close()
                    self.browser.switch_to.window(self.browser.window_handles[0])
            except Exception:
                pass
            return HtmlResponse(url=url, status=403, request=request)

    ### DEPRECATED
    # def process_request(self, request, spider):
    #     url = request.url
    #
    #     # 检查是否是 JSON API 请求
    #     is_json = request.meta.get("is_json", False)
    #
    #     wait_by = request.meta.get("selenium_wait_by", By.CSS_SELECTOR)
    #     wait_target = request.meta.get("selenium_wait_target", "body")
    #     wait_time = request.meta.get("selenium_wait_time", 30)
    #
    #     try:
    #         # 1. 打开一个空白页或新标签
    #         self.browser.execute_script('window.open("about:blank");')
    #         self.browser.switch_to.window(self.browser.window_handles[-1])
    #
    #         if is_json:
    #             # 2. 如果是 JSON API，先导向同源域名以携带 Cookie 和绕过跨域，然后用 JS 发送真实的 POST 请求
    #             # 注意：这里先跳转到主站，确保过掉 Azure 的外部盾
    #             if "nccgroup.com" not in self.browser.current_url:
    #                 self.browser.get("https://www.nccgroup.com/")
    #
    #             # 获取 Scrapy request 携带的 body (Payload)
    #             payload_str = request.body.decode('utf-8') if request.body else "{}"
    #
    #             # 构造前端 fetch 脚本，将结果直接写到 body 里
    #             js_script = f"""
    #             fetch("{url}", {{
    #                 method: "{request.method}",
    #                 headers: {{
    #                     "Content-Type": "application/json"
    #                 }},
    #                 body: `{payload_str}`
    #             }})
    #             .then(response => response.text())
    #             .then(text => {{ document.body.innerText = text; }})
    #             .catch(err => {{ document.body.innerText = "ERROR: " + err; }});
    #             """
    #             self.browser.execute_script(js_script)
    #
    #             # 3. 【核心等待】等待 body 里的内容变成合法的 JSON 格式（以 {{ 开始，以 }} 结束）
    #             WebDriverWait(self.browser, wait_time).until(
    #                 lambda driver: driver.find_element(By.TAG_NAME, "body").text.strip().startswith("{")
    #             )
    #
    #             # 直接获取纯文本 JSON
    #             html = self.browser.find_element(By.TAG_NAME, "body").text.strip()
    #         else:
    #             # 4. 普通 HTML 页面请求逻辑保持不变
    #             self.browser.get(url)
    #             WebDriverWait(self.browser, wait_time).until(
    #                 EC.presence_of_element_located((wait_by, wait_target))
    #             )
    #             html = self.browser.page_source
    #
    #         # 5. 拿到数据后，立刻关闭当前标签页
    #         self.browser.close()
    #
    #         if self.browser.window_handles:
    #             self.browser.switch_to.window(self.browser.window_handles[0])
    #
    #         # 返回响应
    #         return HtmlResponse(url=url,
    #                             body=html,
    #                             request=request,
    #                             encoding='utf-8',
    #                             status=200)
    #
    #     except Exception as e:
    #         MiddleWareLog.info(f"浏览器出现异常 {e}")
    #         try:
    #             if len(self.browser.window_handles) > 1:
    #                 self.browser.close()
    #                 self.browser.switch_to.window(self.browser.window_handles[0])
    #         except Exception:
    #             pass
    #         return HtmlResponse(url=url, status=403, request=request)
    #
    def spider_closed(self, spider):
        # 9. 当爬虫功德圆满结束时，彻底退出并杀死 chrome 进程
        MiddleWareLog.info("爬虫结束，正在关闭 Selenium 全局浏览器...")
        if self.browser:
            self.browser.quit()


# class SeleniumMiddleware(object):
#
#     def __init__(self):
#         MiddleWareLog.info("启用Selenium下载器")
#
#         # 配置 ChromeOptions
#         self.options = Options()
#         # self.options.add_argument('--headless=new')
#         self.options.add_argument('--no-sandbox')
#         self.options.add_argument('--ignore-certificate-errors')
#         self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
#         self.options.add_experimental_option('excludeSwitches', ['enable-logging'])
#         self.options.add_argument('--allow-insecure-localhost')
#         self.options.add_argument('--disable-web-security')
#         self.options.add_argument('--disable-gpu')  # 禁用 GPU，加速无头模式渲染
#         self.options.add_argument('--disable-dev-shm-usage')  # 防止内存不足错误
#         self.options.add_argument('--window-size=1920x1080')  # 指定窗口大小以避免页面渲染异常
#         self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
#
#
#
#     def process_request(self, request, spider):
#         # browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
#
#         url = request.url
#
#         try:
#             self.browser.get(url)
#
#             WebDriverWait(self.browser, 20).until(
#                 EC.presence_of_element_located((By.CSS_SELECTOR, "body"))  # 修改为页面上需要的关键元素
#             )
#
#             html = browser.page_source
#             return HtmlResponse(url=request.url,
#                                 body=html,
#                                 request=request,
#                                 encoding='utf-8',
#                                 status=200)
#         except Exception as e:
#             return HtmlResponse(status=403)
#
#         finally:
#             self.browser.close()


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
