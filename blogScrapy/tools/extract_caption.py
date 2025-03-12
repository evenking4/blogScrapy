import re
import os
import json
import tqdm


def extract_images_from_md(report_dir):
    # 正则匹配 Markdown 图片
    img_pattern1 = re.compile(r'!\[(.*?)\]\((\S+?)\)(.*)$')
    img_pattern2 = re.compile(r'\[!\[(.+?)\]\((\S+?)\)\]\((\S+?)\)(.*)$')

    img_infos = []
    with open(os.path.join(report_dir, 'img_infos.json'), 'r', encoding='utf-8') as f:
        img_infos = json.load(f)

    img_dict = {img_info['image_urls']: {'dir': img_info['dir'], 'filename': img_info['filename']} for img_info in img_infos}

    with open(os.path.join(report_dir, 'content.md'), 'r', encoding='utf-8') as f:
        for line in f:
            search = re.search(img_pattern2, line)
            if search:
                image_url = search.group(1)
                img_path = search.group(2)
                link_url = search.group(3)
                caption = search.group(4).strip()
                img_dict[image_url]['caption'] = caption
                print("Pattern2:")
                # print("image_url:", image_url)
                # print("img_path:", img_path)
                # print("link_url", link_url)
                print(type(caption), "caption:", caption)
            else:
                search = re.search(img_pattern1, line)
                if search:
                    image_url = search.group(1)
                    img_path = search.group(2)
                    caption = search.group(3)
                    img_dict[image_url]['caption'] = caption
                    print("Pattern1:")
                    # print("image_url:", image_url)
                    # print("img_path:", img_path)
                    print(type(caption), "caption:", caption)
    new_img_infos = []
    for image_urls, img_info in img_dict.items():
        try:
            dir = img_info['dir']
            filename = img_info['filename']
            img_caption = img_info['caption']
            new_img_infos.append({'image_urls': image_urls,
                                  'dir': dir,
                                  'filename': filename,
                                  'img_caption': img_caption})
        except Exception as e:
            print(f'Error in {dir}/{filename}')
            print(f'Error is {e}')
            exit(1)

    print(new_img_infos)


if __name__ == '__main__':
    # website_names = ['crowdstrike']
    # for website_name in website_names:
    #     all_uuids = set()
    #     for root, dirs, files in os.walk(f'./main_content/{website_name}'):
    #         all_uuids = set(dirs)
    #         break
    #     for uuid in all_uuids:
    #         extract_images_from_md(f'main_content/{website_name}/{uuid}')
    extract_images_from_md(f'main_content/crowdstrike/e79e232858704023ab52fcbb887b2d31')
