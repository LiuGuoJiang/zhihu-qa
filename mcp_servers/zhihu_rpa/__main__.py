#!/usr/bin/env python3
"""
知乎RPA MCP服务器入口
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcp_servers.zhihu_rpa.server import main

if __name__ == "__main__":
    asyncio.run(main())
