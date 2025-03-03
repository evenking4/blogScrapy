import scrapy
from scrapy.http import Request, Response
from bs4 import BeautifulSoup
import html2text
import hashlib
import json
from tqdm import tqdm
from lxml import etree
from urllib.parse import urlparse, urljoin
from scrapy import signals
from uuid import uuid4
import threading
import logging
import os
from twisted.internet.defer import Deferred
from typing import TYPE_CHECKING, Any, cast

# Comment 增加了链接去重功能

website_name = 'unit42'

# 弃用，已改为自动解析
domain = "https://unit42.paloaltonetworks.com"

img_num = 0

err_blog_num = 0

def hash_string(text, algorithm="sha256"):
    # 计算字符串的哈希值
    hash_func = hashlib.new(algorithm)  # 创建哈希对象
    hash_func.update(text.encode('utf-8'))  # 更新哈希对象
    return hash_func.hexdigest()  # 返回16进制摘要

def is_absolute_url(url: str):
    return url.startswith(('http://', 'https://', 'www'))



if __name__ == '__main__':
    all_uuids = set()

    err_uuids = set()

    for root, dirs, files in os.walk(f'./raw_html/{website_name}'):
        all_uuids = set(dirs)
        break

    # 设置进度条
    link_bar = tqdm(total=len(all_uuids), desc='fumo勤劳工作中 ᗜˬᗜ...', unit="page")

    for uuid in all_uuids:

        try:
            with open(f'raw_html/{website_name}/{uuid}/raw.html', "r", encoding="utf-8") as f:
                html_content = f.read()

            with open(f'raw_html/{website_name}/{uuid}/other.json', "r", encoding="utf-8") as f:
                info = json.load(f)
                blog_url = info['url']
        except Exception as e:
            print(f"在读取{uuid}的文件内容时出现错误：{str(e)}")

        parsed_url = urlparse(blog_url)
        domain = f'{parsed_url.scheme}://{parsed_url.netloc}'


        # 解析
        dom = etree.HTML(html_content)
        soup = BeautifulSoup(html_content, "html.parser")

        title = dom.xpath('//div[@class="ab__title"]//h1/text()')

        if not title:
            print(f'未获取到{uuid}的文章标题')

        if len(title) > 1:
            print(f'{uuid}中解析到多个标题')

        title = ' '.join(title) if title else ''
        # print('title:', title)

        tags = dom.xpath('//div[@class="be__tags-wrapper"]/ul[@role="list"]/li/a/text()')
        # print('tags:', tags)

        date = dom.xpath('//ul[@class="ab__features"]/li[2]/div/text()')
        date = date[0] if date else ''
        # print('date:', date)

        main_soup = soup.find(name="div",
                              class_=["be__contents-wrapper"])

        if not main_soup:
            err_blog_num += 1
            err_uuids.add(uuid)
            print(f"未获取到{uuid}的文章主元素")
            continue


        # 保存图片信息
        img_infos = []
        for img in main_soup.find_all(name='img'):

            if img.get('src') is None and img.get('data-src') is None:
                print(f"OMG, Find a img without src and data-src, it's his uuid:{uuid}")
                continue

            img_num += 1

            if img.get('data-src'):
                image_url = img["data-src"] if is_absolute_url(img["data-src"]) else urljoin(domain, img.get('data-src'))
            else:
                image_url = img["src"] if is_absolute_url(img["src"]) else urljoin(domain, img.get('src'))


            img_info = {
                'image_urls': image_url,
                'dir': f'main_content/{website_name}/{uuid}/img/',
                'filename': hash_string(image_url) + '.jpg'
            }

            img['src'] = 'img/' + img_info['filename']
            img['alt'] = img_info['image_urls']

            img_infos.append(img_info)

        # 配置html2text处理器
        main_extracter = html2text.HTML2Text()
        main_extracter.body_width = 0

        text_content = main_extracter.handle(str(main_soup))

        output_dir = f'main_content/{website_name}/{uuid}/'
        os.makedirs(output_dir, exist_ok=True)
        try:
            with open(output_dir + 'content.md', 'w', encoding='utf-8') as f:
                f.write(text_content)

            with open(output_dir + 'info.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'url': blog_url,
                    'title': title,
                    'tags': tags,
                    'date': date,
                    'text': text_content
                }, f, indent=4)

            with open(output_dir + 'img_infos.json', 'w', encoding='utf-8') as f:
                json.dump(img_infos, f, indent=4)

        except Exception as e:
            print(f'在保存blog {uuid}的信息时出现错误{str(e)}')
        link_bar.update(1)

    with open(f'main_content/{website_name}/err_uuids.json', 'w', encoding='utf-8') as f:
        json.dump(list(err_uuids), f, indent=4)
    print(f'共有{err_blog_num}篇blog在匹配正文时出现问题')
    print(f'共匹配到{img_num}张图片')
