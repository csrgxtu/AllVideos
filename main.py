import asyncio
from calendar import c
from playwright.async_api import async_playwright

async def scrape_douyin(url):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        contexts = browser.contexts
        if not contexts:
            print("No contexts found.")
            return
        context = contexts[0]
        page = await context.new_page()
        # 访问抖音用户主页
        await page.goto(url)
        await page.wait_for_selector('ul[data-e2e="scroll-list"]', timeout=30000)  # 等待页面加载成功，增加超时时间

        # 点击聚焦后才能成功滚动
        await page.click('ul[data-e2e="scroll-list"]')

        # 滚动页面，加载更多视频
        while True:
            print('Scrolling down...')
            await page.keyboard.press('PageDown')
            await page.wait_for_timeout(1000)  # 等待页面加载更多视频

            # 检查是否出现“暂时没有更多了”的文案
            no_more_text = await page.evaluate('document.body.innerText.includes("暂时没有更多了")')
            if no_more_text:
                print("Reached the end of the content.")
                break  # 如果找到文本，停止滚动

        # 滚动结束后获取页面源代码
        page_source = await page.content()

        # 提取 data-e2e="scroll-list" 下的所有 li 元素中的 p 和 a
        extracted_data = await page.evaluate('''() => {
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

        # 打印提取的数据
        for data in extracted_data:
            print(data)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(scrape_douyin('https://www.douyin.com/user/MS4wLjABAAAApz_lA6T5B00ucLSe8Wlk1i-yOa6lXhkZ6gyRjavy7nI'))
