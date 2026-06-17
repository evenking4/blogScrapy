#!/usr/bin/env python3
"""
对比 links 和 old_links 目录中对应网站的链接数据，统计增量变化。

用法:
    python compare_links.py            # 统计 DEFAULT_SITES 中的所有网站
    python compare_links.py darknet    # 仅统计指定网站
"""

import os
import sys

# 全局变量：链接文件夹路径
LINKS_DIR = os.path.join(os.path.dirname(__file__), "../links")
OLD_LINKS_DIR = os.path.join(os.path.dirname(__file__), "../old_links")

# 全局变量：默认统计的网站列表
DEFAULT_SITES = ["darknet"]


def load_links(dir_path, site):
    """读取指定网站的链接文件，返回 {url: digest} 字典。"""
    file_path = os.path.join(dir_path, site, f"{site}.txt")
    if not os.path.exists(file_path):
        print(f"[警告] 文件不存在: {file_path}")
        return {}
    links = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2:
                digest, url = parts
                links[url] = digest
    return links


def compare_site(site):
    """对比单个网站的链接数据并打印统计结果。"""
    old_links = load_links(OLD_LINKS_DIR, site)
    new_links = load_links(LINKS_DIR, site)

    old_urls = set(old_links.keys())
    new_urls = set(new_links.keys())

    intersection = old_urls & new_urls
    old_only = old_urls - new_urls
    new_only = new_urls - old_urls

    print(f"========== {site} ==========")
    print(f"  old_links 链接总数:         {len(old_links)}")
    print(f"  links 链接总数:             {len(new_links)}")
    print(f"  交集（新旧共有）:           {len(intersection)}")
    print(f"  仅在 old_links 中（已移除）: {len(old_only)}")
    print(f"  仅在 links 中（新增）:      {len(new_only)}")
    print()

    return {
        "site": site,
        "old_count": len(old_links),
        "new_count": len(new_links),
        "intersection": len(intersection),
        "old_only": len(old_only),
        "new_only": len(new_only),
    }


def main():
    if len(sys.argv) > 1:
        sites = [sys.argv[1]]
    else:
        sites = DEFAULT_SITES

    results = []
    for site in sites:
        results.append(compare_site(site))

    # 如果统计多个网站，输出汇总行
    if len(results) > 1:
        print("========== 汇总 ==========")
        print(f"{'网站':<25} {'old':>6} {'new':>6} {'交集':>6} {'仅old':>6} {'仅new':>6}")
        for r in results:
            print(
                f"{r['site']:<25} "
                f"{r['old_count']:>6} "
                f"{r['new_count']:>6} "
                f"{r['intersection']:>6} "
                f"{r['old_only']:>6} "
                f"{r['new_only']:>6}"
            )


if __name__ == "__main__":
    main()
