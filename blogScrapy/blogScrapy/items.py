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
