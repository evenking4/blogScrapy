# BlogScrapy

## 环境要求

python版本: 3.11.2

依赖包: `pip install -r requirements.txt`

## 项目结构
```commandline
|- blogScrapy
    |- blogScrapy
        |- spiders
            |- <websitename>_link.py      # 获取对应网站链接的爬虫
            |- ...
            |- html_crwal.py    # 获取链接后，根据链接爬取html原网页的爬虫
            |- img_crawl.py     # 解析完html后，爬取main_content中每个report对应图片的爬虫
        |- ...          # 爬虫组件
    |- extracter
        |- <websitename>_extract.py     # 将report的原始html网页提取main_content和图片信息的脚本
        |- ...
    |- links        # (数据部分，不包含在代码仓库中) 存储网站中需要爬取的文章的链接
        |- <websitename>
            |- <websitename>.txt    # 格式为每一行: <uuid> <url>
    |- raw_html     # (数据部分，不包含在代码仓库中) 存储网站中report的原html网页
        |- <websitename>
            |- <uuid>
                |- raw.html     # report原始html网页
                |- other.json   # 网站的一些额外信息
    |- main_content     # (数据部分，不包含在代码仓库中) 存储解析后的report和img索引及img
        |- <websitename>
            |- <uuid>
                |- img      # img文件夹
                    |- xxx.jpg  # img文件
                    |- ...
                |- content.md   # report正文
                |- info.json    # report的一些信息如title, tags, date
                |- img_infos.json   # report中所有的图片的信息和url
```

## 关于使用Selenium爬取图片
注：由于该方法爬取图片较慢，请仅针对那些爬取率已为0的网站使用。
使用方法：
将settings.py中的DOWNLOADER_MIDDLEWARES中的"blogScrapy.middlewares.SeleniumImageDownloaderMiddleware": 400取消注释，如下所示即可
```python
DOWNLOADER_MIDDLEWARES = {
   "blogScrapy.middlewares.SeleniumImageDownloaderMiddleware": 400,
   # "blogScrapy.middlewares.SeleniumMiddleware": 500,
   # "blogScrapy.middlewares.PauseMiddleware": 600,
}
```
之后运行img_crawl时开头日志出现`MiddleWare - INFO - Selenium Img Crawl Start...`表示添加成功

## 关于服务器爬取图片的指南（省流版）
1. 参考上面配置好环境
2. 将main_content文件夹放置到对应位置
3. 参考以下脚本进行爬取
```bash
#!/bin/bash

# scrapy crawl img_crawl -a target=ciscoumbrella
# scrapy crawl img_crawl -a target=cloudflare
# scrapy crawl img_crawl -a target=crowdstrike
# scrapy crawl img_crawl -a target=csoonline
scrapy crawl img_crawl -a target=darknet
scrapy crawl img_crawl -a target=fireeye
# scrapy crawl img_crawl -a target=forcepoint
# scrapy crawl img_crawl -a target=fsecure
scrapy crawl img_crawl -a target=hotforsecurity
scrapy crawl img_crawl -a target=kaspersky_threat
scrapy crawl img_crawl -a target=kaspersky_vulnerability
scrapy crawl img_crawl -a target=kasperskydaily
scrapy crawl img_crawl -a target=levelblue
scrapy crawl img_crawl -a target=malwarebytes
scrapy crawl img_crawl -a target=mcafee
scrapy crawl img_crawl -a target=nccgroup
scrapy crawl img_crawl -a target=paloalto
scrapy crawl img_crawl -a target=rsa
scrapy crawl img_crawl -a target=securelist
scrapy crawl img_crawl -a target=sophos
scrapy crawl img_crawl -a target=spiderlabs
scrapy crawl img_crawl -a target=symantecthreatintelligence
scrapy crawl img_crawl -a target=thehackernews
scrapy crawl img_crawl -a target=threatpost
scrapy crawl img_crawl -a target=trendmicro
# scrapy crawl img_crawl -a target=trendmicro_malware
# scrapy crawl img_crawl -a target=trendmicro_spam
scrapy crawl img_crawl -a target=trustwave
scrapy crawl img_crawl -a target=unit42
scrapy crawl img_crawl -a target=zscaler
```

## 常用命令
注: 下面的命令中的<>代表你需要指定的参数

1. 爬取对应网站所有文章的链接:
`scrapy crawl <websitename>_link`
成功执行后会在links文件夹中生成一个对应网站名字的文件夹存储爬取到的链接

2. 爬取一个网站链接对应的网页:
`scrapy crawl html_crawl -a target=<websitename>`
成功执行后会在raw_html文件夹中生成一个对应网站名字的文件夹存储爬取到的网页

3. 提取一个网站的主要内容和图片信息（已弃用）
`python extracter/<websitename>_extract.py`
成功执行后会在main_content文件夹中生成一个对应网站名字的文件夹存储report的正文、相关信息、图片信息

4. 爬取一个网站的report的所有图片（已弃用）
`scrapy crawl img_crawl -a target=<websitename>`
成功执行后main_content/<websitename>/<uuid>的report如果有图片则会生成一个img文件夹存放图片

5. 提取一个网站的标题、日期、主要内容
`python extracter/common_extract.py <websitename>`
需要在payloads/extract_target.json中预填网页目标元素XPATH信息
