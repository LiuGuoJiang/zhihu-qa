#!/usr/bin/env python3
"""
热度分数计算器
用于评估知乎问题的热度
"""
import json
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any


def calculate_hot_score(stats: Dict[str, Any]) -> float:
    """
    计算问题热度分数

    算法：
    热度 = (关注数*2 + 回答数*3 + 浏览数*0.001) * 时间衰减因子

    时间衰减因子：
    - 1天内：1.0
    - 1-3天：0.8
    - 3-7天：0.6
    - 7-14天：0.4
    - 14-30天：0.2
    - 30天以上：0.1

    Args:
        stats: 问题统计数据，包含 followers, answers, views, created_at

    Returns:
        热度分数
    """
    followers = stats.get('followers', 0)
    answers = stats.get('answers', 0)
    views = stats.get('views', 0)

    # 计算基础分数
    base_score = followers * 2 + answers * 3 + views * 0.001

    # 计算时间衰减因子
    created_at_str = stats.get('created_at')
    if created_at_str:
        try:
            # 尝试多种日期格式
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    created_at = datetime.strptime(created_at_str[:19], fmt)
                    break
                except ValueError:
                    continue
            else:
                created_at = datetime.now()

            days_ago = (datetime.now() - created_at).days

            if days_ago <= 1:
                time_decay = 1.0
            elif days_ago <= 3:
                time_decay = 0.8
            elif days_ago <= 7:
                time_decay = 0.6
            elif days_ago <= 14:
                time_decay = 0.4
            elif days_ago <= 30:
                time_decay = 0.2
            else:
                time_decay = 0.1
        except Exception:
            time_decay = 0.5  # 默认衰减
    else:
        time_decay = 0.5  # 无时间信息时的默认衰减

    return base_score * time_decay


def calculate_viral_potential(question_data: Dict[str, Any]) -> float:
    """
    计算问题爆款潜力

    评估维度：
    1. 共鸣度 (30%)
    2. 争议性 (20%)
    3. 时效性 (30%)
    4. 专业性 (20%)

    Args:
        question_data: 问题数据

    Returns:
        爆款潜力分数 (0-100)
    """
    # 这里是一个简化的评估逻辑
    # 实际使用中，可以通过LLM分析问题内容来得到更准确的评分

    title = question_data.get('title', '').lower()
    excerpt = question_data.get('excerpt', '').lower()

    # 共鸣度评估
    resonance_keywords = ['薪资', '面试', 'offer', '跳槽', '职业', '焦虑',
                        '内卷', '996', '裁员', '晋升', '成长']
    resonance = min(100, sum(10 for kw in resonance_keywords if kw in title or kw in excerpt))

    # 争议性评估
    controversy_keywords = ['对比', '哪个更好', 'vs', '区别', '选择', '争议']
    controversy = min(100, sum(15 for kw in controversy_keywords if kw in title or kw in excerpt))

    # 时效性评估（基于创建时间）
    created_at_str = question_data.get('created_at')
    if created_at_str:
        try:
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    created_at = datetime.strptime(created_at_str[:19], fmt)
                    break
                except ValueError:
                    continue
            days_ago = (datetime.now() - created_at).days
            if days_ago <= 1:
                timeliness = 100
            elif days_ago <= 3:
                timeliness = 80
            elif days_ago <= 7:
                timeliness = 60
            elif days_ago <= 14:
                timeliness = 40
            else:
                timeliness = 20
        except Exception:
            timeliness = 50
    else:
        timeliness = 50

    # 专业性评估（基于问题分类和关键词）
    professional_keywords = ['架构', '算法', '原理', '实现', '优化', '设计']
    professional = min(100, sum(10 for kw in professional_keywords if kw in title or kw in excerpt))

    # 计算综合爆款潜力
    viral_potential = (
        resonance * 0.3 +
        controversy * 0.2 +
        timeliness * 0.3 +
        professional * 0.2
    )

    return round(viral_potential, 2)


def batch_calculate(input_data: Dict) -> Dict:
    """
    批量计算问题分数

    Args:
        input_data: 输入数据，可以是单个问题或问题列表

    Returns:
        计算结果
    """
    if 'questions' in input_data:
        # 处理问题列表
        questions = input_data['questions']
        for q in questions:
            stats = q.get('stats', {})
            if stats:
                q['hot_score'] = calculate_hot_score(stats)
            q['viral_potential'] = calculate_viral_potential(q)
        return input_data
    else:
        # 处理单个问题
        stats = input_data.get('stats', {})
        if stats:
            input_data['hot_score'] = calculate_hot_score(stats)
        input_data['viral_potential'] = calculate_viral_potential(input_data)
        return input_data


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="知乎问题热度计算器")
    parser.add_argument('--stats', help="问题统计数据(JSON格式)")
    parser.add_argument('--file', help="输入文件路径")
    parser.add_argument('--output', help="输出文件路径")

    args = parser.parse_args()

    # 读取输入数据
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    elif args.stats:
        input_data = json.loads(args.stats)
    else:
        # 从标准输入读取
        input_data = json.load(sys.stdin)

    # 计算分数
    result = batch_calculate(input_data)

    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
