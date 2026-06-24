# scrapy crawl html_crawl -a target=levelblue   # OK

# scrapy crawl html_crawl -a target=ciscoumbrella   # OK

# scrapy crawl html_crawl -a target=cloudflare      # OK

# scrapy crawl html_crawl -a target=crowdstrike     # OK

# scrapy crawl html_crawl -a target=csoonline       # OK 差922

# scrapy crawl html_crawl -a target=darknet         # OK

# scrapy crawl html_crawl -a target=fireeye         # OK

# scrapy crawl html_crawl -a target=forcepoint      # OK

# scrapy crawl html_crawl -a target=hotforsecurity  # OK 差2

# scrapy crawl html_crawl -a target=kasperskydaily  # OK

# scrapy crawl html_crawl -a target=malwarebytes    # OK

# scrapy crawl html_crawl -a target=mcafee          # OK

# scrapy crawl html_crawl -a target=nccgroup

# scrapy crawl html_crawl -a target=rsa         # OK

# scrapy crawl html_crawl -a target=securelist  # OK

#scrapy crawl html_crawl -a target=sophos -a wait_target='//div[@class="min-h-screen"]'
scrapy crawl html_crawl -a target=sophos -a wait_target="//div[@class='min-h-screen']"

# scrapy crawl html_crawl -a target=spiderlabs  # OK

# scrapy crawl html_crawl -a target=symantecthreatintelligence      # OK

# scrapy crawl html_crawl -a target=thehackernews   # OK

# scrapy crawl html_crawl -a target=threatpost  # OK

# scrapy crawl html_crawl -a target=trendmicro

# scrapy crawl html_crawl -a target=unit42_paloalto

# scrapy crawl html_crawl -a target=welivesecurity

# scrapy crawl html_crawl -a target=zscaler

# scrapy crawl html_crawl -a target=kaspersky_threat

# scrapy crawl html_crawl -a target=kaspersky_vulnerability

# scrapy crawl html_crawl -a target=trendmicro_malware  # OK

# scrapy crawl html_crawl -a target=trendmicro_spam     # OK

# scrapy crawl html_crawl -a target=fsecure     #OK

