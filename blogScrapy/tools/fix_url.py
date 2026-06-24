# 本脚本是发现有一个爬取的链接未加协议://域名前缀，需要简单修改一下

if __name__ == '__main__':
    with open("links/sophos/sophos.bak", "r", encoding="utf-8") as f:
        content = f.read()
        links = {line.split(' ')[0]: line.split(' ')[1] for line in content.split('\n') if line}

    with open("links/sophos/sophos.txt", "w", encoding="utf-8") as f:
        for key, value in links.items():

            ############# Core #############
            value = "https://www.sophos.com" + value

            f.write(key + " " + value + "\n")