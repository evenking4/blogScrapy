from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from uuid import uuid4
import time

article_base_url = "https://www.zscaler.com"

max_page = 114

def scrape_blog_links(start_url, next_button_xpath, article_link_xpath):
    # Initialize Selenium WebDriver
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(start_url)
    all_links = []  # Store all unique article links

    try:
        for i in range(0, max_page + 1):
            # Wait for the page to load and locate article links
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, article_link_xpath))
            )

            # Extract article links
            page_links = driver.find_elements(By.XPATH, article_link_xpath)
            print(page_links)
            print(f"第{i}次获取到{len(page_links)}个文章链接")
            all_links.extend(page_links)

            print(f"Collected {len(page_links)} links from current page. Total links: {len(all_links)}")

            # Check if the "Next" button is available
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located((By.XPATH, next_button_xpath))
                )
                time.sleep(2)
                # Click the "Next" button
                next_button = driver.find_element(By.XPATH, next_button_xpath)
                # break
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)  # Wait for the next page to load
            except Exception as e:
                print("Exception:", e)
                print("No more pages to navigate. Scraping completed.")
                break

    finally:
        driver.quit()

    return all_links


if __name__ == "__main__":
    # Define the starting URL and XPaths
    start_url = "https://www.zscaler.com/blogs?type=security-research"  # Replace with the actual blog URL
    article_link_xpath = '//p[@class="text-darkBlue typography-cta mt-auto pt-30"]/a'  # Adjust based on the site's structure
    next_button_xpath = '//div[@class="col-span-full mt-40"]/ul/li[@title="Next Page"]/button'  # Adjust based on the site's structure

    links = scrape_blog_links(start_url, next_button_xpath, article_link_xpath)
    print(f"共获取到{len(links)}个链接")
    links = list(set(links))
    print(f"去重后链接共有{len(links)}个")
    for link in links:
        with open("zscaler_link.txt", "a", encoding='utf-8') as f:
            f.write(uuid4().hex + " " + link + "\n")
