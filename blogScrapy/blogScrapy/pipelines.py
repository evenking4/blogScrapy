# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .items import *
from uuid import uuid1
import json
import os


# class BlogscrapyPipeline:
#     def process_item(self, item, spider):
#         return item


class ArticleLinkPipeline:
    def open_spider(self, spider):
        self.website_name = spider.website_name
        output_dir = f'./links/{self.website_name}/'
        os.makedirs(output_dir, exist_ok=True)
        self.file = open(output_dir + self.website_name + '.txt', 'w')

    def process_item(self, item, spider):
        # print("Receive a item, class:", type(item))
        if isinstance(item, CsoArticleLink):
            self.file.write(item['url'] + '\n')
        else:
            return item

    def close_spider(self, spider):
        self.file.close()


class ArticleContentPipeline:
    def open_spider(self, spider):
        self.website_name = spider.website_name
        self.output_dir = f'./main_text_extract/{self.website_name}/'
        os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        if isinstance(item, CsoArticleContent):
            try:
                with open(self.output_dir + item['filename'], "w", encoding='utf-8') as f:
                    f.write(item['title'])
                    for content in item['contents']:
                        f.write(content + '\n')
            except Exception as e:
                print(f"保存来自url:{item['url']}的文件{item['filename']}时出现错误：{e}")
                try:
                    temp_dir = f'./temp_file/{self.website_name}/'
                    os.makedirs(temp_dir, exist_ok=True)
                    target_path = temp_dir + str(uuid1()) + '.txt'
                    with open(target_path, "w", encoding='utf-8') as f:
                        f.write(item['title'])
                        for content in item['contents']:
                            f.write(content + '\n')
                    print(f"来自url:{item['url']}的{item['filename']}已另存为{target_path}")
                except Exception as e:
                    print(f"另存来自url:{item['url']}的文件{item['filename']}时出现错误：{e}")

        else:
            return item

