import asyncio
import json
import os
import random
from socket import timeout
import time
from calendar import c
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from playwright._impl._errors import TimeoutError

# Define the path for the data file
DATA_FILE = 'extracted_data.json'

async def scrape_douyin(url):
    extracted_data = []  # Initialize the list to store extracted data

    # Check if the data file exists
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)
        print('Data loaded from file.')

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        contexts = browser.contexts
        if not contexts:
            print("No contexts found.")
            return
        context = contexts[0]
        page = await context.new_page()

        if not extracted_data:
            # 访问抖音用户主页
            await page.goto(url)
            await page.wait_for_selector('ul[data-e2e="scroll-list"]', timeout=30000)  # 等待页面加载成功，增加超时时间

            # 点击聚焦后才能成功滚动
            await page.mouse.move(100, 100)
            await page.click('span:has-text("作品")')  # 点击内容为作品的span元素

            while True:
                print('Scrolling down...')
                await page.mouse.wheel(0, 500)  # 向下滚动500像素
                await page.wait_for_timeout(1000)  # 等待页面加载更多视频

                # 检查是否出现“暂时没有更多了”的文案
                no_more_text = await page.evaluate('document.body.innerText.includes("暂时没有更多了")')
                if no_more_text:
                    print("Reached the end of the content.")
                    break  # 如果找到文本，停止滚动

                # 提取 data-e2e="scroll-list" 下的所有 li 元素中的 p 和 a
                data = await page.evaluate('''() => {
                    const items = [];
                    const listItems = document.querySelectorAll('ul[data-e2e="scroll-list"] li');
                    listItems.forEach(item => {
                        const pElement = item.querySelector('p');
                        const aElement = item.querySelector('a');
                        items.push({
                            text: pElement ? pElement.innerText : null,
                            href: aElement ? aElement.href : null
                        });
                    });
                    return items;
                }''')
                extracted_data.extend(data)  # Add the extracted data to the list

            # Save extracted data to a file
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, ensure_ascii=False, indent=4)
            print('Data saved to file.')

        # 打印提取的数据
        for data in extracted_data:
            # 随机休息3到8秒
            time.sleep(random.randint(3, 8))
            # 打开每个href并提取视频链接
            if data['href']:
                await page.goto(data['href'])
                try:
                    await page.wait_for_selector('video', timeout=30000)  # 等待video元素出现
                    print('Video element found.')
                    page_content = await page.content()  # 获取页面内容
                    soup = BeautifulSoup(page_content, 'html.parser')  # 解析页面内容
                    video_element = soup.find('video')  # 查找video元素
                    source_element = video_element.find('source') if video_element else None  # 查找第一个source元素
                    video_link = source_element['src'] if source_element else None  # 获取src链接
                    # 打印原始数据和视频链接
                    print({"text": data['text'], "href": data['href'], "video_link": video_link})
                except TimeoutError:
                    print(f"Timeout while waiting for video on {data['href']}")  # Log the timeout error

        await browser.close()

if __name__ == '__main__':
    asyncio.run(scrape_douyin('https://www.douyin.com/user/MS4wLjABAAAAIaPqhEag0d1HY4qNpo7ad0ffz1rF565v4dN84g05g4vEkjjyBBocLyRG56-yWCaE'))
    # asyncio.run(scrape_douyin('https://www.douyin.com/user/MS4wLjABAAAApz_lA6T5B00ucLSe8Wlk1i-yOa6lXhkZ6gyRjavy7nI'))
