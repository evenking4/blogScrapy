from datetime import datetime
from pathlib import Path
import shutil
import json
import re
import os

from tqdm import tqdm

def check_cve_pattern(text):
    cve_pattern = r'\bCVE-\d{4}-\d{4,}\b'
    
    # 只匹配有无，提高效率
    match = re.search(cve_pattern, text)
    
    #cve_list = re.findall(cve_pattern, text)
    return True if match else False

def copy_to_dir(src, dest):
    src_path = Path(src)
    dest_path = Path(dest) / src_path.name
    
    if dest_path.exists():
        print(f"跳过: {dest_path} 已存在")
        return

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if src_path.is_dir():
            shutil.copytree(src_path, dest_path)
        else:
            shutil.copy2(src_path, dest_path)
    except Exception as e:
        print(f"复制失败: {e}")


def main():
    # statistics target
    totle_websites_num = 0
    totle_blogs_num = 0
    totle_cve_blogs_num = 0
    yearly_blogs = {}
    yearly_cve_blogs = {}
    

    with open('payloads/websites.json', 'r', encoding='utf-8') as f:
        websites = json.load(f)

    websites.remove('apt_notes')

    totle_websites_num = len(websites)

    for website in tqdm(websites):
        for root, dirs, files in os.walk(f'main_content/{website}'):
            blog_uuids = set(dirs)
            break
        print(website)

        for blog_uuid in tqdm(blog_uuids):
            with open(f'main_content/{website}/{blog_uuid}/info.json', 'r', encoding='utf-8') as f:
                blog_info = json.load(f)
            
            title = blog_info['title']
            year = datetime.strptime(blog_info['date'], "%Y-%m-%d").year
            main_content = blog_info['text']

            yearly_blogs[year] = yearly_blogs.setdefault(year, 0) + 1

            if check_cve_pattern(title) or check_cve_pattern(main_content):
                yearly_cve_blogs[year] = yearly_cve_blogs.setdefault(year, 0) + 1
                copy_to_dir(f'main_content/{website}/{blog_uuid}', f'cve_blogs/')


    
    print("每年blog总数：")
    for k, v in sorted(yearly_blogs.items(), key=lambda x: x[0], reverse=True):
        print(f'{k} : {v}')
        totle_blogs_num += v

    print("每年含CVE的blog总数：")
    for k, v in sorted(yearly_cve_blogs.items(), key=lambda x: x[0], reverse=True):
        print(f'{k} : {v}')
        totle_cve_blogs_num += v

    print(f"website总数： {totle_websites_num}")
    print(f"blog总数： {totle_blogs_num}")
    print(f"含CVE的blog总数： {totle_cve_blogs_num}")


if __name__ == '__main__':
    main()