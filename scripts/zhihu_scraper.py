#!/usr/bin/env python3
"""
知乎数据抓取辅助脚本
通过MCP服务器被调用，或被智能体直接使用
"""
import httpx
import json
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin


@dataclass
class QuestionStats:
    """问题统计数据"""
    question_id: str
    title: str
    followers: int = 0
    answers: int = 0
    views: int = 0
    created_at: Optional[str] = None


@dataclass
class Question:
    """问题数据模型"""
    question_id: str
    title: str
    url: str
    author: str
    excerpt: str = ""
    created_at: Optional[str] = None
    question_type: str = "search"
    invitation_count: int = 0
    stats: Optional[Dict[str, int]] = None


class ZhihuScraper:
    """知乎数据抓取器"""

    def __init__(self, cookie: str, base_url: str = "https://www.zhihu.com/api/v3"):
        self.cookie = cookie
        self.base_url = base_url
        self.client = httpx.Client(
            headers={
                "Cookie": cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
            timeout=30.0,
            follow_redirects=True
        )

    def search_questions(
        self,
        keyword: str,
        category: str = "tech",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索知乎问题

        Args:
            keyword: 搜索关键词
            category: 问题分类（tech/general等）
            limit: 返回数量限制

        Returns:
            问题列表
        """
        params = {
            "q": keyword,
            "type": "content",
            "limit": limit
        }
        try:
            response = self.client.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            return self._parse_search_results(response.json())
        except Exception as e:
            print(f"搜索出错: {e}", file=sys.stderr)
            return []

    def get_question_stats(self, question_id: str) -> QuestionStats:
        """
        获取问题统计数据

        Args:
            question_id: 问题ID

        Returns:
            问题统计数据
        """
        try:
            response = self.client.get(f"{self.base_url}/questions/{question_id}")
            response.raise_for_status()
            data = response.json()
            return QuestionStats(
                question_id=question_id,
                title=data.get("title", ""),
                followers=data.get("follower_count", 0),
                answers=data.get("answer_count", 0),
                views=data.get("visit_count", 0),
                created_at=data.get("created", "")
            )
        except Exception as e:
            print(f"获取问题统计出错: {e}", file=sys.stderr)
            return QuestionStats(question_id=question_id, title="")

    def get_hot_answers(
        self,
        question_id: str,
        min_votes: int = 100,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取热门回答

        Args:
            question_id: 问题ID
            min_votes: 最小赞同数
            limit: 返回数量限制

        Returns:
            热门回答列表
        """
        try:
            params = {"limit": limit, "order_by": "votes"}
            response = self.client.get(
                f"{self.base_url}/questions/{question_id}/answers",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            answers = data.get("data", [])
            return [
                {
                    "answer_id": a.get("id"),
                    "author": a.get("author", {}).get("name", "匿名"),
                    "author_id": a.get("author", {}).get("id", ""),
                    "content": a.get("content", "")[:500],  # 截取前500字符
                    "voteup_count": a.get("voteup_count", 0),
                    "comment_count": a.get("comment_count", 0),
                    "url": f"https://www.zhihu.com/question/{question_id}/answer/{a.get('id')}"
                }
                for a in answers
                if a.get("voteup_count", 0) >= min_votes
            ]
        except Exception as e:
            print(f"获取热门回答出错: {e}", file=sys.stderr)
            return []

    def get_creator_center_questions(
        self,
        question_type: str = "all",
        limit: int = 20
    ) -> Dict[str, List[Dict]]:
        """
        获取创作中心 - 等你来答的问题

        Args:
            question_type: 'invited'(邀请回答), 'recommended'(推荐问题), 'all'(全部)
            limit: 返回数量限制

        Returns:
            {
                "invited": [邀请回答的问题列表],
                "recommended": [推荐的问题列表]
            }
        """
        result = {"invited": [], "recommended": []}

        try:
            # 获取邀请回答的问题
            if question_type in ["invited", "all"]:
                invited_response = self.client.get(
                    f"{self.base_url}/creator/invitations",
                    params={"limit": limit}
                )
                if invited_response.status_code == 200:
                    invited_data = invited_response.json().get("data", [])
                    result["invited"] = [
                        asdict(self._parse_creator_question(item, "creator_invited"))
                        for item in invited_data
                    ]

            # 获取推荐的问题
            if question_type in ["recommended", "all"]:
                recommended_response = self.client.get(
                    f"{self.base_url}/creator/recommendations",
                    params={"limit": limit}
                )
                if recommended_response.status_code == 200:
                    recommended_data = recommended_response.json().get("data", [])
                    result["recommended"] = [
                        asdict(self._parse_creator_question(item, "creator_recommended"))
                        for item in recommended_data
                    ]
        except Exception as e:
            print(f"获取创作中心问题出错: {e}", file=sys.stderr)

        return result

    def get_invitation_questions(self, limit: int = 20) -> List[Dict]:
        """获取邀请回答的问题列表（快捷方法）"""
        result = self.get_creator_center_questions("invited", limit)
        return result.get("invited", [])

    def _parse_search_results(self, search_data: Dict) -> List[Dict]:
        """解析搜索结果"""
        questions = []
        for item in search_data.get("data", []):
            if item.get("type") == "question":
                obj = item.get("object", {})
                question = Question(
                    question_id=str(obj.get("id", "")),
                    title=obj.get("title", ""),
                    url=f"https://www.zhihu.com/question/{obj.get('id')}",
                    author=obj.get("author", {}).get("name", "匿名用户"),
                    excerpt=obj.get("excerpt", "")[:200]
                )
                questions.append(asdict(question))
        return questions

    def _parse_creator_question(self, item: Dict, q_type: str) -> Question:
        """解析创作中心返回的问题数据"""
        question = item.get("question", {})
        author = item.get("author", {})
        return Question(
            question_id=str(question.get("id", "")),
            title=question.get("title", ""),
            url=f"https://www.zhihu.com/question/{question.get('id')}",
            author=author.get("name", "匿名用户"),
            excerpt=question.get("excerpt", "")[:200],
            created_at=question.get("created_time"),
            question_type=q_type,
            invitation_count=item.get("invitation_count", 0)
        )

    def close(self):
        """关闭客户端连接"""
        self.client.close()


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="知乎数据抓取工具")
    parser.add_argument("cookie", help="知乎Cookie")
    parser.add_argument("command", choices=["search", "creator", "invitations", "stats", "answers"],
                       help="执行的命令")
    parser.add_argument("args", nargs="*", help="命令参数")

    args = parser.parse_args()

    scraper = ZhihuScraper(args.cookie)

    try:
        if args.command == "search":
            keyword = args.args[0] if len(args.args) > 0 else ""
            limit = int(args.args[1]) if len(args.args) > 1 else 20
            result = scraper.search_questions(keyword, limit=limit)

        elif args.command == "creator":
            q_type = args.args[0] if len(args.args) > 0 else "all"
            limit = int(args.args[1]) if len(args.args) > 1 else 20
            result = scraper.get_creator_center_questions(q_type, limit)

        elif args.command == "invitations":
            limit = int(args.args[0]) if len(args.args) > 0 else 20
            result = scraper.get_invitation_questions(limit)

        elif args.command == "stats":
            question_id = args.args[0] if len(args.args) > 0 else ""
            result = asdict(scraper.get_question_stats(question_id))

        elif args.command == "answers":
            question_id = args.args[0] if len(args.args) > 0 else ""
            min_votes = int(args.args[1]) if len(args.args) > 1 else 100
            result = scraper.get_hot_answers(question_id, min_votes)

        else:
            result = {"error": "Unknown command"}

        print(json.dumps(result, ensure_ascii=False, indent=2))

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
