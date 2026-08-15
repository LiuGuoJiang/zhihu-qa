#!/usr/bin/env python3
"""
知乎RPA数据抓取脚本 - 使用Playwright模拟真人操作
避免直接调用API，降低被封号风险
"""
import asyncio
import json
import random
import os
import sys
from typing import List, Dict, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser


class ZhihuRPA:
    """知乎RPA操作类 - 模拟真人浏览行为"""

    def __init__(self, headless: bool = True):
        # 从环境变量读取headless设置，默认为True
        env_headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        self.headless = env_headless if headless is None else headless
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None

    async def start(self):
        """启动浏览器"""
        playwright = await async_playwright().start()

        # 使用 Chromium，配置更真实的浏览器指纹
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ]
        )

        # 创建浏览器上下文，配置更真实的用户代理
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )

        # 添加初始化脚本，隐藏自动化特征
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en']
            });
        """)

    async def load_session(self):
        """加载已保存的登录会话"""
        session_file = './data/zhihu_session.json'
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                cookies = json.load(f)
                await self.context.add_cookies(cookies)
            return True
        return False

    async def login(self):
        """处理登录 - 如果未登录会跳转到登录页"""
        if not self.page:
            self.page = await self.context.new_page()

        await self.page.goto('https://www.zhihu.com', wait_until='networkidle')

        # 检查是否需要登录
        need_login = await self.page.query_selector('.SignContainer-header')
        if need_login:
            if not self.headless:
                print("=" * 50)
                print("需要登录，请在浏览器中完成登录...")
                print("登录完成后脚本将自动继续")
                print("=" * 50)

            # 等待登录成功（检查是否跳转到首页或出现用户头像）
            try:
                await self.page.wait_for_selector('.GlobalSideBar-avatar, .AppHeader-profile', timeout=120000)
                if not self.headless:
                    print("登录成功！")
            except Exception as e:
                print(f"等待登录超时: {e}")
                return False

        # 保存登录状态
        session_file = './data/zhihu_session.json'
        os.makedirs('./data', exist_ok=True)
        await self.context.storage_state(path=session_file)
        print(f"会话已保存到 {session_file}")

        return True

    async def human_like_scroll(self, scroll_count: int = 3):
        """模拟真人滚动行为 - 随机速度、随机停顿"""
        for i in range(scroll_count):
            scroll_distance = random.randint(200, 500)
            await self.page.evaluate(f'window.scrollBy(0, {scroll_distance})')

            # 随机等待，模拟阅读时间
            await asyncio.sleep(random.uniform(0.5, 2.0))

    async def human_like_wait(self):
        """随机等待，模拟人类操作间隔"""
        await asyncio.sleep(random.uniform(1.0, 3.0))

    async def human_like_mouse_move(self):
        """模拟鼠标移动"""
        try:
            await self.page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600)
            )
            await asyncio.sleep(random.uniform(0.1, 0.3))
        except:
            pass

    async def get_creator_center_questions(
        self,
        question_type: str = "invited",
        limit: int = 20
    ) -> Dict[str, List[Dict]]:
        """
        获取创作中心等你来答的问题（RPA方式）

        Args:
            question_type: 'invited' | 'recommended' | 'all'
            limit: 返回数量限制
        """
        result = {"invited": [], "recommended": []}

        if not self.page:
            await self.start()
            self.page = await self.context.new_page()

        # 访问创作中心
        await self.page.goto('https://www.zhihu.com/creator', wait_until='networkidle')
        await self.human_like_wait()

        # 点击"等你来答"标签
        try:
            # 尝试多种选择器匹配可能的页面结构
            selectors = [
                'text=等你来答',
                'a:has-text("等你来答")',
                '[data-tab="creator-mono"]',
            ]
            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    await element.click()
                    break
                except:
                    continue

            await self.page.wait_for_load_state('networkidle')
            await self.human_like_scroll(2)
        except Exception as e:
            print(f"点击等你来答失败: {e}")
            # 尝试直接访问邀请回答页面
            await self.page.goto('https://www.zhihu.com/creator/mono/answer?status=inviting', wait_until='networkidle')
            await self.human_like_wait()

        # 获取邀请回答的问题
        if question_type in ["invited", "all"]:
            try:
                # 等待问题列表加载
                await self.page.wait_for_selector('.ContentItem, .QuestionItem, .CreatorQuestionItem', timeout=10000)

                # 模拟滚动加载更多
                for _ in range(3):
                    await self.human_like_scroll(2)
                    await asyncio.sleep(1)

                # 获取所有问题元素
                questions = await self.page.query_selector_all('.ContentItem, .QuestionItem, .CreatorQuestionItem')
                print(f"找到 {len(questions)} 个问题")

                for q in questions[:limit]:
                    question_data = await self._parse_question_element(q)
                    if question_data:
                        result["invited"].append(question_data)
            except Exception as e:
                print(f"获取邀请回答失败: {e}")

        print(f"获取到 {len(result['invited'])} 个邀请回答的问题")
        return result

    async def _parse_question_element(self, element) -> Dict:
        """解析问题元素"""
        try:
            # 尝试多种选择器获取标题
            title_selectors = ['.ContentItem-title', '.QuestionItem-title', '.CreatorQuestionItem-title', 'a[class*="title"]']
            title = None
            title_text = ""

            for selector in title_selectors:
                try:
                    title = await element.query_selector(selector)
                    if title:
                        title_text = await title.inner_text()
                        break
                except:
                    continue

            if not title_text:
                # 尝试从链接获取
                link = await element.query_selector('a')
                if link:
                    title_text = await link.inner_text()

            # 获取链接
            link = await element.query_selector('a')
            href = await link.get_attribute('href') if link else ""
            question_id = href.split('/')[-1] if href else ""

            return {
                "question_id": question_id,
                "title": title_text.strip() if title_text else "",
                "url": f"https://www.zhihu.com{href}" if href and not href.startswith('http') else href,
                "source": "rpa_creator_center",
                "discovered_at": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"解析问题元素失败: {e}")
            return {}

    async def search_questions(self, keyword: str, limit: int = 20) -> List[Dict]:
        """搜索问题（RPA方式）"""
        if not self.page:
            await self.start()
            self.page = await self.context.new_page()

        # 访问搜索页面
        search_url = f'https://www.zhihu.com/search?type=content&q={keyword}'
        await self.page.goto(search_url, wait_until='networkidle')
        await self.human_like_wait()
        await self.human_like_scroll(2)

        questions = []
        try:
            # 尝试多种搜索结果选择器
            selectors = ['.SearchResult-Card', '.ContentItem', '.List-item']
            results = []

            for selector in selectors:
                try:
                    items = await self.page.query_selector_all(selector)
                    if items:
                        results = items
                        break
                except:
                    continue

            for item in results[:limit]:
                question_data = await self._parse_search_result(item)
                if question_data:
                    questions.append(question_data)
        except Exception as e:
            print(f"搜索解析失败: {e}")

        print(f"搜索到 {len(questions)} 个相关问题")
        return questions

    async def _parse_search_result(self, element) -> Optional[Dict]:
        """解析搜索结果"""
        try:
            # 获取标题
            title_selectors = ['.SearchResult-title', '.ContentItem-title', 'a[class*="title"]']
            title_text = ""
            for selector in title_selectors:
                try:
                    title = await element.query_selector(selector)
                    if title:
                        title_text = await title.inner_text()
                        break
                except:
                    continue

            # 获取链接
            link = await element.query_selector('a')
            href = await link.get_attribute('href') if link else ""

            # 获取摘要
            excerpt_selectors = ['.SearchResult-excerpt', '.ContentItem-excerpt', '.ContentItem-summary']
            excerpt_text = ""
            for selector in excerpt_selectors:
                try:
                    excerpt = await element.query_selector(selector)
                    if excerpt:
                        excerpt_text = await excerpt.inner_text()
                        excerpt_text = excerpt_text[:200]  # 限制长度
                        break
                except:
                    continue

            return {
                "title": title_text.strip() if title_text else "",
                "url": f"https://www.zhihu.com{href}" if href and not href.startswith('http') else href,
                "excerpt": excerpt_text.strip() if excerpt_text else "",
                "source": "rpa_search",
                "discovered_at": datetime.now().isoformat()
            }
        except Exception as e:
            return None

    async def get_question_answers(self, question_url: str, min_votes: int = 100) -> List[Dict]:
        """获取问题下的回答（RPA方式）"""
        if not self.page:
            await self.start()
            self.page = await self.context.new_page()

        await self.page.goto(question_url, wait_until='networkidle')
        await self.human_like_wait()
        await self.human_like_scroll(4)  # 滚动加载更多回答

        answers = []
        try:
            # 尝试多种回答列表选择器
            selectors = ['.List-item', '.AnswerItem', '[class*="Answer"]']
            answer_items = []

            for selector in selectors:
                try:
                    items = await self.page.query_selector_all(selector)
                    if items:
                        answer_items = items
                        break
                except:
                    continue

            for item in answer_items:
                try:
                    # 获取赞同数
                    vote_up = await item.query_selector('.VoteButton--up, [class*="VoteButton"]')
                    vote_text = await vote_up.inner_text() if vote_up else "0"
                    vote_count = self._parse_vote_count(vote_text)

                    if vote_count >= min_votes:
                        # 获取作者
                        author_selectors = ['.AuthorInfo-name, .AuthorInfo-name a, [class*="Author"]']
                        author_name = "匿名"
                        for selector in author_selectors:
                            try:
                                author = await item.query_selector(selector)
                                if author:
                                    author_name = await author.inner_text()
                                    break
                            except:
                                continue

                        # 获取内容
                        content_selectors = ['.RichContent-inner, .Answer-content, [class*="RichContent"]']
                        content_text = ""
                        for selector in content_selectors:
                            try:
                                content = await item.query_selector(selector)
                                if content:
                                    content_text = await content.inner_text()
                                    content_text = content_text[:500]  # 限制长度
                                    break
                            except:
                                continue

                        answers.append({
                            "author": author_name.strip() if author_name else "匿名",
                            "vote_count": vote_count,
                            "content": content_text,
                            "source": "rpa_question_page"
                        })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"获取回答失败: {e}")

        print(f"获取到 {len(answers)} 个高赞回答")
        return answers

    def _parse_vote_count(self, text: str) -> int:
        """解析赞同数（处理"万"、"K"等单位）"""
        text = text.strip().lower()
        if '万' in text:
            return int(float(text.replace('万', '')) * 10000)
        elif 'k' in text:
            return int(float(text.replace('k', '')) * 1000)
        else:
            try:
                # 移除可能的符号
                text = text.replace(',', '').replace(' ', '')
                return int(text)
            except:
                return 0

    async def close(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()


# 同步接口封装（用于命令行调用）
def run_rpa_async(coro):
    """运行异步函数"""
    return asyncio.run(coro)


if __name__ == "__main__":
    async def main():
        # 检查命令行参数
        if len(sys.argv) < 2:
            print("Usage: python zhihu_rpa.py <command> [args...]")
            print("Commands:")
            print("  invitations             - 获取邀请回答的问题")
            print("  search <keyword>        - 搜索问题")
            print("  answers <url>           - 获取问题回答")
            print("  login                   - 登录并保存会话")
            print()
            print("Environment Variables:")
            print("  HEADLESS=false           - 使用有头模式（可以看到浏览器）")
            sys.exit(1)

        command = sys.argv[1]

        # 创建RPA实例
        rpa = ZhihuRPA()

        try:
            await rpa.start()

            # 尝试加载已保存的会话
            session_loaded = await rpa.load_session()
            if session_loaded:
                print("已加载已保存的登录状态")
            else:
                print("未找到保存的会话，需要登录")
                await rpa.login()

            # 执行命令
            if command == "login":
                # 重新登录
                await rpa.login()
                print("登录成功，会话已保存")

            elif command == "invitations":
                result = await rpa.get_creator_center_questions("invited")
                print(json.dumps(result, ensure_ascii=False, indent=2))

            elif command == "search":
                if len(sys.argv) < 3:
                    print("Error: search command requires keyword argument")
                    sys.exit(1)
                keyword = sys.argv[2]
                result = await rpa.search_questions(keyword)
                print(json.dumps(result, ensure_ascii=False, indent=2))

            elif command == "answers":
                if len(sys.argv) < 3:
                    print("Error: answers command requires URL argument")
                    sys.exit(1)
                url = sys.argv[2]
                result = await rpa.get_question_answers(url)
                print(json.dumps(result, ensure_ascii=False, indent=2))

            else:
                print(f"Unknown command: {command}")
                sys.exit(1)

        except KeyboardInterrupt:
            print("\n操作已取消")
        except Exception as e:
            print(f"执行出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await rpa.close()

    run_rpa_async(main())
