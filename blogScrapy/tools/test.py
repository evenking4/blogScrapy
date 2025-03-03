import sys
import os
from collections import defaultdict

def deduplicate_links(target):
    input_file = f"links/{target}/{target}.txt"
    output_file = f"links/{target}/{target}_new.txt"

    if not os.path.exists(input_file):
        print(f"Error: File {input_file} does not exist.")
        return

    # Read and process links
    links = []
    updated_links = []

    with open(input_file, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            parts = line.split(' ')

            links.append({"uuid": parts[0], "url": parts[1]})

    updated_links = list({link['url']: link for link in links}.values())

    print(f"总共有链接{len(links)}个")
    print(f"去重后有链接{len(updated_links)}个")



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <target>")
        sys.exit(1)

    target = sys.argv[1]
    deduplicate_links(target)