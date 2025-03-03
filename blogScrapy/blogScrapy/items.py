# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BlogscrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class CsoArticleLink(scrapy.Item):
    url = scrapy.Field()


class CsoArticleContent(scrapy.Item):
    filename = scrapy.Field()
    title = scrapy.Field()
    contents = scrapy.Field()
    url = scrapy.Field()


class JsonItem(scrapy.Item):
    uuid = scrapy.Field()
    url = scrapy.Field()
    website = scrapy.Field()
    filename = scrapy.Field()
    data = scrapy.Field()


class RawHtmlItem(scrapy.Item):
    uuid = scrapy.Field()
    url = scrapy.Field()
    website = scrapy.Field()
    filename = scrapy.Field()
    html = scrapy.Field()

class BinItem(scrapy.Item):
    uuid = scrapy.Field()
    url = scrapy.Field()
    website = scrapy.Field()
    filename = scrapy.Field()
    data = scrapy.Field()

class LinkItem(scrapy.Item):
    uuid = scrapy.Field()
    website = scrapy.Field()
    url = scrapy.Field()

class ImgItem(scrapy.Item):
    dir = scrapy.Field()
    filename = scrapy.Field()
    image_urls = scrapy.Field()
    appendix = scrapy.Field()
    retry_cnt = scrapy.Field()

class DictItem(scrapy.Item):
    dir = scrapy.Field()
    filename = scrapy.Field()
    data = scrapy.Field()

