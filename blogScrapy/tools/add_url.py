import os
import json

# 此脚本用于为main_content/website/uuid/info.json中添加url字段
# 由于添加url字段是在写提取器时为了方便查看后面加的，所以前面的几个main_content中没有


if __name__ == '__main__':

    website_names = set()
    for root, dirs, files in os.walk('./main_content'):
        website_names = set(dirs)
        break

    for website_name in website_names:

        all_uuids = set()
        for root, dirs, files in os.walk(f'./main_content/{website_name}'):
            all_uuids = set(dirs)
            break

        for uuid in all_uuids:
            try:
                with open(f'./main_content/{website_name}/{uuid}/info.json', 'r', encoding='utf-8') as f:
                    content_info = json.load(f)

                # 已有url的则跳过
                if content_info.get('url') is not None:
                    continue

                with open(f'./raw_html/{website_name}/{uuid}/other.json', 'r', encoding='utf-8') as f:
                    raw_info = json.load(f)

                content_info = {'url': raw_info['url'], **content_info}

                with open(f'./main_content/{website_name}/{uuid}/info.json', 'w', encoding='utf-8') as f:
                    json.dump(content_info, f, indent=4)

            except Exception as e:
                print(f'读取{website_name}/{uuid}时出现错误:{str(e)}')