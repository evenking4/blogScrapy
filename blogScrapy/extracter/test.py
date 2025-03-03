from bs4 import BeautifulSoup

html = """ 
<html>
    <body>
        <div class="content test">div - 内容1</div>
        <div id="main">div - 内容2</div>
        <p class="content">p - 内容3</p>
        <p id="main">p - 内容4</p>
        <span class="other">span - 内容5</span>
    </body>
</html>
"""

soup = BeautifulSoup(html, "html.parser")

# 查找 <div> 或 <p>，且 class="content" 或 id="main"
tags = soup.find_all(["div", "p"], class_="test")
for tag in tags:
    print(tag.name, ":", tag.text)
