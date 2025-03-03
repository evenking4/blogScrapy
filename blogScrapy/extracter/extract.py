import html2text
import os
from bs4 import BeautifulSoup
from lxml import etree
from uuid import uuid4
import requests

domian = 'https://www.forcepoint.com/'

website = 'forcepoint'

blog_uuid = '0ae35726f67343c5b8caffe5b2eccd6e'

file_path = f'./raw_html/{website}/{blog_uuid}/raw.html'

output_dir = f'./main_content/{website}/{blog_uuid}/'



def extract_content(html):
    dom = etree.HTML(html)
    soup = BeautifulSoup(html, "html.parser")

    title = dom.xpath('//h1/text()')[0]
    print('title:', title)

    tags = dom.xpath('//ul[@class="flex flex-wrap gap-3 md:justify-end"]/li/a/text()')
    print('tags:', tags)

    main_soup = soup.find(name="div",
                          class_="relative flex flex-col-reverse md:flex-row md:items-start md:gap-lg xl:gap-xl mx-auto max-w-screen-lg")

    if not main_soup:
        print(f"未获取到{blog_uuid}的文章主元素")

    for img in main_soup.find_all(name='img'):
        img_url = domian + img["src"]
        img_folder = f'main_content/{website}/{blog_uuid}/img/'
        img_filename = uuid4().hex + '.jpg'

        os.makedirs(img_folder, exist_ok=True)

        response = requests.get(img_url)
        if response.status_code == 200:

            with open(img_folder + img_filename, "wb") as f:
                f.write(response.content)

        img['src'] = 'img/' + img_filename
        img['alt'] = 'myAlt'


    # 配置html2text处理器
    main_extracter = html2text.HTML2Text()
    main_extracter.body_width = 0
    # main_extracter = MainHTML2Text()
    # main_extracter.body_width = 0

    text_content = main_extracter.handle(str(main_soup))

    os.makedirs(output_dir, exist_ok=True)
    with open(output_dir + 'content.md', 'w', encoding='utf-8') as f:
        f.write(text_content)

    # elements = dom.xpath('//h1 | //div[@class="relative flex flex-col-reverse md:flex-row md:items-start md:gap-lg xl:gap-xl mx-auto max-w-screen-lg"]//p')
    # print(elements)
    # cropped_html = "".join([etree.tostring(ele, encoding='unicode') for ele in elements])
    # print(cropped_html)
    # return cropped_html



if __name__ == '__main__':
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    cropped_html = extract_content(html_content)

# text_content = html2text.html2text(cropped_html)
#
#
# os.makedirs(output_dir, exist_ok=True)
# with open(output_dir + 'content.md', 'w', encoding='utf-8') as f:
#     f.write(text_content)

