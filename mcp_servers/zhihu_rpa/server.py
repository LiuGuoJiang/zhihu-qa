#!/usr/bin/env python3
"""
知乎RPA MCP服务器
将RPA功能封装为MCP工具，供Paperclip智能体调用
"""
import asyncio
import json
import os
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from scripts.zhihu_rpa import ZhihuRPA


class ZhihuRPAMCP:
    """知乎RPA MCP服务封装"""

    def __init__(self):
        self.server = Server("zhihu-rpa")
        self.rpa: ZhihuRPA = None
        self._setup_tools()

    def _setup_tools(self):
        """注册MCP工具"""

        @self.server.tool()
        async def get_invitation_questions(limit: int = 20) -> str:
            """获取邀请回答的问题列表"""
            try:
                if not self.rpa:
                    self.rpa = ZhihuRPA()
                    await self.rpa.start()
                    await self.rpa.load_session()

                result = await self.rpa.get_creator_center_questions("invited", limit)
                return json.dumps({
                    "success": True,
                    "data": result,
                    "count": len(result.get("invited", []))
                }, ensure_ascii=False, indent=2)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

        @self.server.tool()
        async def get_recommended_questions(limit: int = 20) -> str:
            """获取推荐的问题列表"""
            try:
                if not self.rpa:
                    self.rpa = ZhihuRPA()
                    await self.rpa.start()
                    await self.rpa.load_session()

                result = await self.rpa.get_creator_center_questions("recommended", limit)
                return json.dumps({
                    "success": True,
                    "data": result,
                    "count": len(result.get("recommended", []))
                }, ensure_ascii=False, indent=2)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

        @self.server.tool()
        async def search_questions(keyword: str, limit: int = 20) -> str:
            """搜索知乎问题"""
            try:
                if not self.rpa:
                    self.rpa = ZhihuRPA()
                    await self.rpa.start()
                    await self.rpa.load_session()

                result = await self.rpa.search_questions(keyword, limit)
                return json.dumps({
                    "success": True,
                    "data": result,
                    "count": len(result)
                }, ensure_ascii=False, indent=2)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

        @self.server.tool()
        async def get_question_answers(question_url: str, min_votes: int = 100) -> str:
            """获取问题下的高赞回答"""
            try:
                if not self.rpa:
                    self.rpa = ZhihuRPA()
                    await self.rpa.start()
                    await self.rpa.load_session()

                result = await self.rpa.get_question_answers(question_url, min_votes)
                return json.dumps({
                    "success": True,
                    "data": result,
                    "count": len(result)
                }, ensure_ascii=False, indent=2)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

        @self.server.tool()
        async def login() -> str:
            """执行知乎登录（有头模式）"""
            try:
                # 登录需要使用有头模式
                self.rpa = ZhihuRPA(headless=False)
                await self.rpa.start()
                success = await self.rpa.login()
                await self.rpa.close()
                self.rpa = None

                return json.dumps({
                    "success": success,
                    "message": "登录成功，会话已保存" if success else "登录失败"
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

        @self.server.tool()
        async def close_browser() -> str:
            """关闭浏览器实例"""
            try:
                if self.rpa:
                    await self.rpa.close()
                    self.rpa = None
                return json.dumps({"success": True, "message": "浏览器已关闭"}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    async def run(self):
        """运行MCP服务器"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialize_options()
            )


async def main():
    mcp = ZhihuRPAMCP()
    await mcp.run()


if __name__ == "__main__":
    asyncio.run(main())
