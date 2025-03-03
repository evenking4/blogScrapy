# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .items import *
import time
import logging
from uuid import uuid1
import json
import os
import json
from scrapy.pipelines.images import ImagesPipeline
from scrapy.http.request import Request
import logging


pipelineLog = logging.getLogger("PipelineLog")

# 设置日志输出
os.makedirs(f'log/PipelineLog', exist_ok=True)
file_handler = logging.FileHandler(f'log/PipelineLog/log.txt', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

pipelineLog.addHandler(file_handler)
pipelineLog.addHandler(stream_handler)

pipelineLog.debug("###################Start###################")

# class BlogscrapyPipeline:
#     def process_item(self, item, spider):
#         return item

PipelineLog = logging.getLogger("Pipeline")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
PipelineLog.addHandler(stream_handler)


# 弃用
class ArticleLinkPipeline:
    def open_spider(self, spider):
        self.website_name = getattr(spider, 'website_name', None)
        if self.website_name:
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
        if hasattr(self, 'file'):
            self.file.close()


class ArticleContentPipeline:
    def open_spider(self, spider):
        self.website_name = getattr(spider, 'website_name', None)
        if self.website_name:
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


class JsonPipeline:
    def open_spider(self, spider):
        self.website_name = getattr(spider, 'website_name', None)
        if self.website_name:
            self.output_dir = f'./json_data/{self.website_name}/'
            os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        if isinstance(item, JsonItem):
            file_dir = self.output_dir + item['uuid'] + '/'
            os.makedirs(file_dir, exist_ok=True)
            try:
                with open(file_dir + item['filename'], "w", encoding='utf-8') as f:
                    json.dump(json.loads(item['data']), f, indent=4)

                # 将其他信息写入一个json文件中
                with open(file_dir + "other.json", "w", encoding='utf-8') as f:
                    item.pop("html", None)
                    json.dump(dict(item), f, indent=4)
            except Exception as e:
                print(f"保存文件{file_dir + item['filename']}时出现错误：{e}")

        else:
            return item


class HtmlPipeline:
    def open_spider(self, spider):
        self.website_name = getattr(spider, 'website_name', None)
        if self.website_name:
            self.output_dir = f'./raw_html/{self.website_name}/'
            os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        if isinstance(item, RawHtmlItem):
            file_dir = self.output_dir + item['uuid'] + '/'
            os.makedirs(file_dir, exist_ok=True)
            try:
                with open(file_dir + item['filename'], "w", encoding='utf-8') as f:
                    f.write(item['html'])

                # 将其他信息写入一个json文件中
                with open(file_dir + "other.json", "w", encoding='utf-8') as f:
                    item.pop("html", None)
                    json.dump(dict(item), f, indent=4)
            except Exception as e:
                print(f"保存文件{file_dir + item['filename']}时出现错误：{e}")

        else:
            return item

class BinPipeline:
    def open_spider(self, spider):
        self.website_name = getattr(spider, 'website_name', None)
        if self.website_name:
            self.output_dir = f'./raw_html/{self.website_name}/'
            os.makedirs(self.output_dir, exist_ok=True)

    def process_item(self, item, spider):
        if isinstance(item, BinItem):
            file_dir = self.output_dir + item['uuid'] + '/'
            os.makedirs(file_dir, exist_ok=True)
            try:
                with open(file_dir + item['filename'], "wb") as f:
                    f.write(item['data'])

                # 将其他信息写入一个json文件中
                with open(file_dir + "other.json", "w", encoding='utf-8') as f:
                    item.pop("data", None)
                    json.dump(dict(item), f, indent=4)
            except Exception as e:
                print(f"保存文件{file_dir + item['filename']}时出现错误：{e}")

        else:
            return item


# class LinkPipeline:
#     def open_spider(self, spider):
#         self.website_name = getattr(spider, 'website_name', None)
#         if self.website_name:
#             self.output_dir = f'./links/{self.website_name}/'
#             os.makedirs(self.output_dir, exist_ok=True)
#
#             try:
#                 self.file = open(self.output_dir + self.website_name + ".txt", "a", encoding="utf-8")
#             except Exception as e:
#                 print(f"打开网站{self.website_name}的链接文件时出现错误:{e}")
#
#     def process_item(self, item, spider):
#         if isinstance(item, LinkItem):
#             try:
#                 self.file.write(item["uuid"] + " " + item["url"] + "\n")
#             except Exception as e:
#                 print(f"保存链接{item['uuid']}-{item['url']}时出现错误:{e}")
#
#         else:
#             return item
#
#     def close_spider(self, spider):
#         if hasattr(self, 'file'):
#             self.file.close()

class LinkPipeline:

    links = []
    def open_spider(self, spider):
        self.website_name = getattr(spider, 'website_name', None)


    def process_item(self, item, spider):
        if isinstance(item, LinkItem):
            self.links.append({'uuid': item['uuid'], 'url': item['url']})
        else:
            return item

    def close_spider(self, spider):
        if self.website_name and len(self.links) > 0:

            # 创建文件夹
            output_dir = f'./links/{self.website_name}/'
            os.makedirs(output_dir, exist_ok=True)

            # 链接去重
            updated_links = list({link['url']: link for link in self.links}.values())

            duplicated_links = self.links.copy()
            for link in updated_links:
                duplicated_links.remove(link)

            PipelineLog.info(f"共接受到链接{len(self.links)}个")
            PipelineLog.info(f"去重后链接共有{len(updated_links)}个")
            # PipelineLog.info(f"重复的链接如下:{' '.join([link['url'] for link in duplicated_links])}")

            # 写入链接
            try:
                with open(output_dir + self.website_name + ".txt", "a", encoding="utf-8") as file:
                    for link in updated_links:
                        file.write(link["uuid"] + " " + link["url"] + "\n")
            except Exception as e:
                print(f"保存网站{self.website_name}的链接文件时出现错误:{e}")


class ImgPipeline(ImagesPipeline):

    img_num = 0

    err_num = 0

    max_retry = 5

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Accept': '*/*'
    }

    def process_item(self, item, spider):
        if isinstance(item, ImgItem):
            return super().process_item(item, spider)
        else:
            return item

    def get_media_requests(self, item, info):
        return Request(url=item['image_urls'],
                       headers=self.headers)

    def file_path(self, request, item, response=None, info=None):
        return item['dir'] + item['filename']

    def item_completed(self, results, item, info):
        for success, info in results:
            if success:
                self.img_num += 1
                # pipelineLog.info(f"成功下载图片{info['url']}")
            else:
                self.err_num += 1
                pipelineLog.error(f"下载来自{item['image_urls']}的图片时出现错误:{str(info)}\n"
                                  f"附加信息: {str(item['appendix'])}")
                # if item['retry_cnt'] <= self.max_retry:
                #     time.sleep(2)
                #     pipelineLog.info(f"对图片{item['image_urls']}进行第{item['retry_cnt']}次重试")
                #     item['retry_cnt'] += 1
                #     return self.get_media_requests(item, info)
                # else:
                #     pipelineLog.info(f"图片{item['image_urls']}重试次数到达上限")
        return item

    def close_spider(self, spider):
        print(f'共获取到图片{self.img_num}个，获取失败的图片有{self.err_num}个')


class DictPipeline:
    def process_item(self, item, spider):
        if isinstance(item, DictItem):
            os.makedirs(item['dir'], exist_ok=True)
            try:
                with open(item['dir'] + item['filename'], "w", encoding='utf-8') as f:
                    json.dump(item['data'], f, indent=4)
            except Exception as e:
                print(f"保存文件{item['dir'] + item['filename']}时出现错误：{e}\n")

        else:
            return item
