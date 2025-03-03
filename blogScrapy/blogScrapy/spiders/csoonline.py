import scrapy
from scrapy.http import Request, Response
from tqdm import tqdm
from typing import Any
from ..items import *
import uuid
import threading

lock = threading.Lock()

class CsoonlineSpider(scrapy.Spider):
    name = "csoonline"
    website_name = "csoonline"
    allowed_domains = ["www.csoonline.com"]
    start_urls = ["https://www.csoonline.com/asean/security/page/2/"]
    page_base_url = "https://www.csoonline.com/asean/security/page/"

    all_article_links = []

    rename_cnt = 0
    article_cnt = 0

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.linkbar = None

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, dont_filter=True, callback=self.get_page_num)


    def get_page_num(self, response):

        # 根据页面导航栏获取所有页数
        page_num = response.xpath('//*[@id="primary"]/section[2]/div/div[2]/div[14]/nav/ul/li[last()-1]/a/text()').get()
        page_num = int(page_num.replace(",", ""))

        # 小批量调试
        # page_num = 10

        self.linkbar = tqdm(total=page_num, desc='Get Article Links...', unit="page")
        # self.article_bar = None

        for page in range(1, page_num + 1):
            page_url = self.page_base_url + str(page)
            yield Request(page_url, dont_filter=True, callback=self.get_article_link)


    def get_article_link(self, response):
        # 获取当前页面所有文章链接
        # article_links = response.xpath('//*[@id="primary"]/section[2]/div/div[2]/div/a/@href').getall()
        article_links = response.xpath('//div[@class="content-listing-various__container"]/div[@class="content-listing-various__row"]/a/@href').getall()

        # 更新进度条
        self.linkbar.update(1)

        # 爬取链接对应的文章
        for link in article_links:

            # 是否保存文章链接
            if self.settings.get('SAVE_MIDDLE_DATA'):
                item = CsoArticleLink()
                item['url'] = link
                yield item

            # with lock:
            #     # 更新爬取文章的进度条
            #     if self.article_bar is None:
            #         article_bar = tqdm(total=len(article_links), desc="爬取文章进度", unit="篇")
            #     else:
            #         article_bar.total += len(article_links)
            #         article_bar.refresh()

            yield Request(link, dont_filter=True, callback=self.extract_blog_content)

    def extract_blog_content(self, response):

        self.article_cnt += 1

        filename = response.request.url.split('/')[-1]

        if not filename:
            self.rename_cnt += 1
            uid = str(uuid.uuid1())
            filename = "rename-" + uid + ".html"
            print(f"已保存:{self.article_cnt}篇,重命名:{self.rename_cnt},来自url:{response.request.url}的文件被命名为{filename}")

        htmlItem = RawHtmlItem()
        htmlItem['filename'] = filename
        htmlItem['html'] = response.text


        yield htmlItem


        # 解析部分代码
        ####################################################################
        # title = response.xpath('//title/text()').get().strip()
        #
        # subheadline = response.xpath('//h2[@class="content-subheadline"]/text()').get()
        #
        # # contents = response.xpath('//div[contains(@class, "article-column")]//text()').getall()
        #
        # # 爬取正文的中的小标题和段落文字（段落文字中有些超链接元素会将段落隔开，需要进行合并处理）
        # raw_contents = response.xpath('//h2[@class="wp-block-heading"] | //div[@class="article-column__content"]/p')
        # contents = []
        # for raw_content in raw_contents:
        #     if isinstance(raw_content, str):
        #         contents.append(raw_content)
        #     else:
        #         contents.append(''.join(raw_content.xpath('.//text()').getall()))
        # contents = [x.strip() for x in contents if x.strip()]
        #
        # # 有些文章可能没有subheadline
        # if subheadline:
        #     contents.insert(0, subheadline)
        #
        # if not title:
        #     print("title go Wrong.url is:", response.request.url)
        #
        # item = CsoArticleContent()
        # item['filename'] = filename
        # item['title'] = title
        # item['contents'] = contents
        # item['url'] = response.request.url
        #
        # # with lock:
        # #     self.article_bar.update(1)
        #
        # yield item
        ####################################################################


    def parse(self, response):
        pass

    def close(self, reason):
        self.linkbar.close()