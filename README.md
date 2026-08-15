# 知乎问答知识库系统

基于Paperclip平台的智能体协作系统，专注于科技领域的知乎问答内容生产。

**重要说明：** 本系统采用**RPA（浏览器自动化）**方式获取知乎数据，模拟真人操作，避免直接调用API导致封号风险。

## 系统概述

本系统利用Paperclip平台的通用智能体能力（如Claude Code CLI），通过AGENTS.md配置文件定义角色和工作流程，实现：

- **问题发现**：从知乎创作中心"等你来答"和科技话题中发现有价值的问题
- **素材收集**：多渠道收集相关素材并验证可靠性
- **故事化创作**：将素材转化为引人入胜的故事化回答

## 为什么选择RPA？

| 方式 | 优点 | 缺点 |
|------|------|------|
| **API调用** | 速度快，资源消耗少 | 容易被检测和封号 |
| **RPA（本项目采用）** | 模拟真人操作，安全性高 | 速度较慢，需要更多资源 |

**RPA方案优势：**
- ✅ 更安全：模拟真人操作，不易被检测
- ✅ 更稳定：不受API变动影响
- ✅ 更真实：可处理动态加载的内容
- ✅ 会话管理：登录一次，长期复用

## 项目结构

```
zhihu-qa/
├── agents/                    # 各员工的AGENTS.md配置
│   ├── question_scout/       # 问题探索员
│   ├── material_collector/   # 素材研究员
│   └── story_writer/         # 故事创作者
├── skills/                    # 共享技能库
│   ├── zhihu_research.md     # 知乎调研技能
│   ├── story_writing.md      # 故事化写作技能
│   └── tech_analysis.md      # 科技领域分析技能
├── scripts/                   # Python辅助脚本
│   ├── zhihu_rpa.py         # 知乎RPA数据抓取（Playwright）
│   ├── hot_score_calculator.py # 热度计算
│   └── material_classifier.py # 素材分类
├── data/                      # 数据存储
│   ├── questions.json        # 问题库
│   ├── materials/            # 素材存储
│   └── drafts/               # 回答草稿
├── mcp_servers/              # MCP服务器配置
│   ├── knowledge_base/       # 知识库MCP
│   └── zhihu_api/           # 知乎API MCP
├── .paperclip/               # Paperclip配置
│   └── company.yaml         # 公司配置文件
├── requirements.txt
├── .env.example
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，填入必要的配置
```

需要配置的关键变量：
- `PAPERCLIP_API_URL`: Paperclip API地址
- `OPENAI_API_KEY`: OpenAI API密钥（如需使用LLM）

**注意：** RPA方式不需要配置知乎Cookie，首次使用时会引导登录。

### 3. 安装Playwright浏览器

```bash
# 安装Playwright及Chromium浏览器
pip install playwright
playwright install chromium
```

### 4. 首次使用 - 登录知乎

```bash
# 使用有头模式进行首次登录（可以看到浏览器）
HEADLESS=false python scripts/zhihu_rpa.py login

# 浏览器会打开，手动完成登录
# 登录成功后会话保存到 data/zhihu_session.json
```

### 5. 测试RPA功能

```bash
# 获取邀请回答的问题
python scripts/zhihu_rpa.py invitations

# 搜索问题
python scripts/zhihu_rpa.py search "GPT-4"

# 获取问题回答
python scripts/zhihu_rpa.py answers "https://www.zhihu.com/question/xxxxx"
```

### 6. 在Paperclip中导入公司配置

```bash
# 通过Paperclip CLI导入
paperclip company import .paperclip/company.yaml
```

## 核心功能

### 问题探索员 (Question Scout)

负责发现知乎上值得回答的科技问题。

**数据来源：**
1. 创作中心"等你来答"（优先级最高）
   - 邀请回答的问题
   - 推荐的问题
2. 科技话题热门问题

**评估标准：**
- 热度分数：关注数、回答数、浏览数的综合计算
- 爆款潜力：共鸣度、争议性、时效性、专业性的评估

### 素材研究员 (Material Collector)

为选定问题收集高质量的素材。

**收集渠道：**
- 知乎高赞回答
- 科技媒体文章（36氪、虎嗅、极客公园等）
- 技术文档和论文
- 内部知识库

**素材分类：**
- `fact_data`: 事实数据
- `expert_opinion`: 专家观点
- `case_study`: 案例故事
- `background`: 背景知识

### 故事创作者 (Story Writer)

将素材转化为故事化的科技回答。

**六段式结构：**
1. 钩子：引人入胜的开头
2. 个人背景：建立可信度
3. 问题/挑战：明确要解决的问题
4. 探索过程：展示解决问题的旅程
5. 解决方案：给出清晰答案
6. 关键收获：总结和行动建议

## 使用RPA脚本

### 基础用法

```bash
# 获取邀请回答的问题
python scripts/zhihu_rpa.py invitations

# 搜索问题
python scripts/zhihu_rpa.py search "GPT-4"

# 获取问题回答
python scripts/zhihu_rpa.py answers "https://www.zhihu.com/question/xxxxx"

# 重新登录
python scripts/zhihu_rpa.py login
```

### 调试模式

```bash
# 有头模式（可以看到浏览器操作）
HEADLESS=false python scripts/zhihu_rpa.py invitations

# 无头模式（默认，生产环境）
python scripts/zhihu_rpa.py invitations
```

### 热度计算

```bash
# 计算单个问题的热度
echo '{"followers":1000,"answers":50,"views":10000,"created_at":"2026-08-14"}' | \
  python scripts/hot_score_calculator.py

# 批量计算
python scripts/hot_score_calculator.py --file data/questions.json --output scored_questions.json
```

### 素材分类

```bash
python scripts/material_classifier.py \
  --input materials.json \
  --output classified.json \
  --keywords GPT-4 AI 大模型
```

## Paperclip集成

### 公司配置

`.paperclip/company.yaml` 定义了：
- 公司使命和目标
- 三个智能体角色及其职责
- 心跳调度配置
- 共享技能定义
- MCP服务器配置

### AGENTS.md

每个智能体的AGENTS.md文件包含：
- 角色定位
- 核心技能和工作流程
- 工具使用方法
- 约束条件
- 质量检查点

### 共享技能

共享技能可以被多个智能体调用：
- `zhihu_research`: 知乎调研技能
- `story_writing`: 故事化写作技能
- `tech_analysis`: 科技领域分析技能

## MCP服务器

### 知识库MCP

提供工具：
- `search`: 搜索知识库中的素材
- `store`: 存储新素材到知识库
- `get`: 根据ID获取素材
- `list`: 列出所有素材

### 知乎API MCP

提供工具：
- `search_questions`: 搜索知乎问题
- `get_question_details`: 获取问题详情
- `get_answers`: 获取问题回答
- `get_creator_center_questions`: 获取创作中心问题
- `get_invitation_questions`: 获取邀请回答列表
- `calculate_hot_score`: 计算热度分数

## 数据格式

### 问题数据格式

```json
{
  "question_id": "unique_id",
  "title": "问题标题",
  "url": "问题链接",
  "author": "提问者",
  "stats": {
    "followers": 关注数,
    "answers": 回答数,
    "views": 浏览数
  },
  "tags": ["标签1", "标签2"],
  "category": "产品分析|技术趋势|编程实践|行业观察",
  "source": "creator_invited|creator_recommended|search",
  "discovered_at": "发现时间",
  "hot_score": 热度分数,
  "status": "pending|processing|materials_ready|draft_ready|completed",
  "viral_potential": 爆款潜力分数
}
```

### 素材数据格式

```json
{
  "question_id": "问题ID",
  "materials": [
    {
      "id": "material_001",
      "type": "fact_data|expert_opinion|case_study|background",
      "source": "来源",
      "url": "链接",
      "title": "标题",
      "author": "作者",
      "summary": "摘要",
      "key_points": ["要点1", "要点2"],
      "relevance_score": 相关度,
      "credibility_score": 可信度
    }
  ]
}
```

## 工作流程

1. **问题发现阶段**
   - question_scout 每小时执行一次
   - 从创作中心和热门话题中筛选问题
   - 计算热度和爆款潜力
   - 保存到 `data/questions.json`

2. **素材收集阶段**
   - material_collector 被新问题触发
   - 多渠道收集相关素材
   - 验证素材质量
   - 保存到 `data/materials/{question_id}.json`

3. **内容创作阶段**
   - story_writer 被素材就绪触发
   - 读取素材并生成故事化回答
   - 保存到 `data/drafts/{question_id}.md`

4. **人工审核**
   - 审核生成的内容质量
   - 必要时进行修改
   - 发布到知乎

## 质量保证

### 问题质量检查
- [ ] 热度分数是否合理
- [ ] 爆款潜力是否>60
- [ ] 是否避免了重复问题
- [ ] 分类是否准确

### 素材质量检查
- [ ] 是否来自可靠来源
- [ ] 可信度是否>0.6
- [ ] 相关性是否>0.6
- [ ] 是否包含多种类型素材

### 内容质量检查
- [ ] 是否遵循六段式结构
- [ ] 是否有引人入胜的开头
- [ ] 技术解释是否通俗易懂
- [ ] 是否有数据支撑
- [ ] 是否有明确的收获和建议

## 后续扩展

MVP验证成功后，可以添加：
- 更多智能体角色（事实核查员、配图设计师）
- 自动发布到知乎的功能
- 内容效果追踪和优化
- 更复杂的MCP工具
- 多领域支持

## 许可证

MIT License
