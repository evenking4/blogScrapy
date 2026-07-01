import sys
import os
import json
from tqdm import tqdm
from lxml import etree
import html2text
from unity import format_time_str

# Generic blog content extractor
# Usage: python common_extract.py <website_name>
# Reads xpath config from payloads/extract_target.json

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python common_extract.py <website_name>")
        sys.exit(1)

    website_name = sys.argv[1]

    # Load extract config
    with open('payloads/extract_target.json', 'r', encoding='utf-8') as f:
        extract_config = json.load(f)

    if website_name not in extract_config:
        print(f"Website '{website_name}' not found in payloads/extract_target.json")
        sys.exit(1)

    config = extract_config[website_name]
    xpath_title = config['title']
    xpath_date = config['date']
    xpath_main = config['main_content']

    # Get all raw_html uuids
    raw_dir = f'./raw_html/{website_name}'
    if not os.path.isdir(raw_dir):
        print(f"Directory {raw_dir} does not exist")
        sys.exit(1)

    all_uuids = set()
    for root, dirs, files in os.walk(raw_dir):
        all_uuids = set(dirs)
        break

    # Get already processed uuids for dedup / resume
    main_dir = f'./main_content/{website_name}'
    processed_uuids = set()
    if os.path.isdir(main_dir):
        for root, dirs, files in os.walk(main_dir):
            processed_uuids = set(dirs)
            break

    # Set difference: only process un-extracted pages
    remaining_uuids = all_uuids - processed_uuids

    print(f"Total raw pages: {len(all_uuids)}")
    print(f"Already processed: {len(processed_uuids)}")
    print(f"Remaining: {len(remaining_uuids)}")

    err_blog_num = 0
    err_blog_id = set()

    link_bar = tqdm(total=len(remaining_uuids), desc=f'Extracting {website_name}', unit="page")

    for uuid in remaining_uuids:
        html_path = f'{raw_dir}/{uuid}/raw.html'
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        dom = etree.HTML(html_content)

        # --- Extract title ---
        title_nodes = dom.xpath(xpath_title)
        title = title_nodes[0].strip() if title_nodes else ''

        if not title:
            print(f"未获取到 {uuid} 的标题")
            err_blog_num += 1
            err_blog_id.add(uuid)
            link_bar.update(1)
            continue

        # --- Extract date ---
        date_nodes = dom.xpath(xpath_date)
        raw_date = date_nodes[0].strip() if date_nodes else ''

        if not raw_date:
            print(f"未获取到 {uuid} 的日期")
            err_blog_num += 1
            err_blog_id.add(uuid)
            link_bar.update(1)
            continue

        date = format_time_str(raw_date)
        if not date:
            err_blog_num += 1
            err_blog_id.add(uuid)
            link_bar.update(1)
            continue

        # --- Extract main_content via XPath, then convert with html2text ---
        main_elements = dom.xpath(xpath_main)
        if not main_elements:
            print(f"未获取到 {uuid} 的文章内容")
            err_blog_num += 1
            err_blog_id.add(uuid)
            link_bar.update(1)
            continue

        # Convert lxml element to HTML string for html2text
        main_html = etree.tostring(main_elements[0], encoding='unicode')

        main_extracter = html2text.HTML2Text()
        main_extracter.body_width = 0
        text_content = main_extracter.handle(main_html)

        if not text_content or not text_content.strip():
            print(f"{uuid} 正文内容缺失")
            err_blog_num += 1
            err_blog_id.add(uuid)
            link_bar.update(1)
            continue

        # --- Write output ---
        output_dir = f'main_content/{website_name}/{uuid}/'
        os.makedirs(output_dir, exist_ok=True)
        try:
            with open(output_dir + 'content.md', 'w', encoding='utf-8') as f:
                f.write(text_content)

            with open(output_dir + 'info.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'title': title,
                    'date': date,
                    'text': text_content
                }, f, indent=4)
        except Exception as e:
            print(f'Error saving blog {uuid}: {str(e)}')

        link_bar.update(1)

    link_bar.close()
    print(f'Done. Total errors: {err_blog_num}')
    if err_blog_id:
        print(f'Error UUIDs: {err_blog_id}')
