{
  "name": "zhihu-rpa",
  "version": "1.0.0",
  "description": "知乎RPA MCP服务器，通过浏览器自动化获取知乎数据",
  "author": "科技内容工作室",

  "server": {
    "command": "python",
    "args": ["-m", "mcp_servers.zhihu_rpa.server"],
    "env": {
      "HEADLESS": "true"
    }
  },

  "tools": [
    {
      "name": "get_invitation_questions",
      "description": "获取知乎创作中心邀请回答的问题列表",
      "parameters": {
        "type": "object",
        "properties": {
          "limit": {
            "type": "integer",
            "description": "返回数量限制",
            "default": 20
          }
        }
      },
      "returns": {
        "success": "是否成功",
        "data": "问题列表",
        "count": "问题数量"
      }
    },
    {
      "name": "get_recommended_questions",
      "description": "获取知乎创作中心推荐的问题列表",
      "parameters": {
        "type": "object",
        "properties": {
          "limit": {
            "type": "integer",
            "description": "返回数量限制",
            "default": 20
          }
        }
      }
    },
    {
      "name": "search_questions",
      "description": "搜索知乎问题",
      "parameters": {
        "type": "object",
        "properties": {
          "keyword": {
            "type": "string",
            "description": "搜索关键词"
          },
          "limit": {
            "type": "integer",
            "description": "返回数量限制",
            "default": 20
          }
        },
        "required": ["keyword"]
      }
    },
    {
      "name": "get_question_answers",
      "description": "获取问题下的高赞回答",
      "parameters": {
        "type": "object",
        "properties": {
          "question_url": {
            "type": "string",
            "description": "问题URL"
          },
          "min_votes": {
            "type": "integer",
            "description": "最小赞同数",
            "default": 100
          }
        },
        "required": ["question_url"]
      }
    },
    {
      "name": "login",
      "description": "执行知乎登录（有头模式，需要手动操作）",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    },
    {
      "name": "close_browser",
      "description": "关闭浏览器实例，释放资源",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    }
  ],

  "settings": {
    "max_concurrent_requests": 1,
    "request_timeout": 300,
    "browser_recycle_interval": 50
  },

  "usage_examples": [
    {
      "description": "获取邀请回答的问题",
      "tool_call": "get_invitation_questions",
      "parameters": {"limit": 20}
    },
    {
      "description": "搜索AI相关问题",
      "tool_call": "search_questions",
      "parameters": {"keyword": "GPT-4", "limit": 10}
    },
    {
      "description": "获取问题回答",
      "tool_call": "get_question_answers",
      "parameters": {"question_url": "https://www.zhihu.com/question/xxxxx", "min_votes": 100}
    }
  ]
}
