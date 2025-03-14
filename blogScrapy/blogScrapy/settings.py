# Scrapy settings for blogScrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# My Config Variable
SAVE_MIDDLE_DATA = True

ROBOTSTXT_OBEY = False

SPLASH_URL = 'http://localhost:8050'

PAUSETIME_429 = 30


BOT_NAME = "blogScrapy"

SPIDER_MODULES = ["blogScrapy.spiders"]
NEWSPIDER_MODULE = "blogScrapy.spiders"

# LOG_LEVEL = "DEBUG"
LOG_LEVEL = "ERROR"
# LOG_LEVEL = "FATAL"
# LOG_ENABLED = False

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "blogScrapy (+http://www.yourdomain.com)"

# Obey robots.txt rules
# ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 10
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "blogScrapy.middlewares.BlogscrapySpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   # "blogScrapy.middlewares.SeleniumImageDownloaderMiddleware": 400,
   # "blogScrapy.middlewares.SeleniumMiddleware": 500,
   # "blogScrapy.middlewares.PauseMiddleware": 600,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
   # "blogScrapy.extensions.PAUSE_429_Extension": 500,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   # "blogScrapy.pipelines.ArticleLinkPipeline": 300,
   # "blogScrapy.pipelines.ArticleContentPipeline": 400,
   "blogScrapy.pipelines.DictPipeline": 400,
   "blogScrapy.pipelines.ImgPipeline": 400,
   "blogScrapy.pipelines.JsonPipeline": 500,
   "blogScrapy.pipelines.HtmlPipeline": 600,
   "blogScrapy.pipelines.BinPipeline": 700,
   "blogScrapy.pipelines.LinkPipeline": 800,
}

IMAGES_STORE = '.'

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
