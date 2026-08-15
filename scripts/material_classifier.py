#!/usr/bin/env python3
"""
素材分类工具
自动对收集的素材进行分类
"""
import json
import sys
import argparse
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Material:
    """素材数据模型"""
    id: str
    type: str
    source: str
    url: str
    title: str
    author: str
    summary: str
    key_points: List[str]
    relevance_score: float = 0.0
    credibility_score: float = 0.0


class MaterialClassifier:
    """素材分类器"""

    # 分类关键词
    CATEGORY_KEYWORDS = {
        'fact_data': ['数据', '统计', '报告', '份额', '增长', '用户', '营收',
                     '性能', '参数', '规格', '价格', '发布', '上线'],
        'expert_opinion': ['观点', '分析', '认为', '预测', '趋势', '判断',
                          '专家', '分析师', '研究员', '表示', '指出'],
        'case_study': ['案例', '实践', '经验', '故事', '项目', '应用',
                      '实施', '落地', '成功', '失败', '尝试'],
        'background': ['背景', '历史', '发展', '起源', '演变', '原理',
                      '概念', '定义', '介绍', '概述', '基础']
    }

    # 可信来源列表
    CREDIBLE_SOURCES = [
        '36kr.com', 'huxiu.com', 'geekpark.net', 'techcrunch.com',
        'zhihu.com', 'github.com', 'arxiv.org', 'mit.edu',
        'gov.cn', 'ieee.org', 'acm.org'
    ]

    def classify(self, material: Dict[str, Any]) -> str:
        """
        对素材进行分类

        Args:
            material: 素材数据

        Returns:
            分类结果
        """
        text = f"{material.get('title', '')} {material.get('summary', '')}"
        text = text.lower()

        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[category] = score

        # 返回得分最高的分类
        return max(scores.items(), key=lambda x: x[1])[0] if max(scores.values()) > 0 else 'background'

    def calculate_relevance(self, material: Dict[str, Any], question_keywords: List[str]) -> float:
        """
        计算素材相关性

        Args:
            material: 素材数据
            question_keywords: 问题关键词列表

        Returns:
            相关性分数 (0-1)
        """
        text = f"{material.get('title', '')} {material.get('summary', '')}".lower()

        # 计算关键词匹配度
        matched_keywords = sum(1 for kw in question_keywords if kw.lower() in text)
        relevance = min(1.0, matched_keywords / max(1, len(question_keywords)))

        return round(relevance, 2)

    def calculate_credibility(self, material: Dict[str, Any]) -> float:
        """
        计算素材可信度

        Args:
            material: 素材数据

        Returns:
            可信度分数 (0-1)
        """
        source = material.get('source', '').lower()
        url = material.get('url', '').lower()

        # 来源可靠性 (40%)
        source_score = 0.0
        if any(credible in source or credible in url for credible in self.CREDIBLE_SOURCES):
            source_score = 1.0
        elif 'edu' in url or 'org' in url:
            source_score = 0.8
        elif 'com' in url:
            source_score = 0.6
        else:
            source_score = 0.4

        # 内容完整性 (30%)
        completeness_score = 0.0
        if material.get('title') and material.get('summary'):
            completeness_score = 1.0
        elif material.get('title') or material.get('summary'):
            completeness_score = 0.5

        # 作者信息 (30%)
        author_score = 0.0
        author = material.get('author', '')
        if author and author != '匿名用户':
            author_score = 1.0
        elif author:
            author_score = 0.5

        credibility = (
            source_score * 0.4 +
            completeness_score * 0.3 +
            author_score * 0.3
        )

        return round(credibility, 2)

    def process_materials(self, materials: List[Dict], question_keywords: List[str]) -> List[Dict]:
        """
        批量处理素材

        Args:
            materials: 素材列表
            question_keywords: 问题关键词列表

        Returns:
            处理后的素材列表
        """
        processed = []
        for material in materials:
            # 分类
            material['type'] = self.classify(material)

            # 计算相关性
            material['relevance_score'] = self.calculate_relevance(material, question_keywords)

            # 计算可信度
            material['credibility_score'] = self.calculate_credibility(material)

            # 只保留高质量素材
            if material['relevance_score'] > 0.6 and material['credibility_score'] > 0.6:
                processed.append(material)

        # 按相关性降序排列
        processed.sort(key=lambda x: x['relevance_score'], reverse=True)

        return processed


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="素材分类工具")
    parser.add_argument('--input', help="输入文件路径")
    parser.add_argument('--output', help="输出文件路径")
    parser.add_argument('--keywords', nargs='+', help="问题关键词列表")

    args = parser.parse_args()

    # 读取输入数据
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    classifier = MaterialClassifier()

    # 处理素材
    materials = data.get('materials', [])
    keywords = args.keywords or []

    processed = classifier.process_materials(materials, keywords)

    result = {
        'question_id': data.get('question_id'),
        'question_title': data.get('question_title'),
        'materials': processed,
        'total_count': len(processed),
        'status': 'ready'
    }

    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
