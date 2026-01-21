#!/usr/bin/env python3
"""
新闻源诊断脚本
快速测试所有新闻源的可访问性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hot_news import *

def test_news_source(source_name, fetch_func, category=None):
    """测试单个新闻源"""
    print(f"\n🔍 测试 {source_name}...")
    try:
        result = fetch_func()
        
        if isinstance(result, list) and result:
            if isinstance(result[0], dict):  # 新格式：列表中的字典
                print(f"   ✅ 成功获取 {len(result)} 条新闻")
                for i, item in enumerate(result[:3], 1):
                    title = item.get('title', str(item))[:50]
                    print(f"      {i}. {title}")
            else:  # 旧格式：直接是标题列表
                print(f"   ✅ 成功获取 {len(result)} 条新闻")
                for i, title in enumerate(result[:3], 1):
                    print(f"      {i}. {title[:50]}")
        else:
            print(f"   ⚠️  获取到空数据")
            
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False
    
    return True

def main():
    print("🚀 开始新闻源诊断测试")
    print("=" * 60)
    
    # 测试基础新闻源
    base_sources = [
        ("人民网", fetch_people_news),
        ("新华网", fetch_xinhua_news),
        ("央视网", fetch_cctv_news),
        ("IT之家", fetch_ithome_news),
        ("微博热搜", fetch_weibo_hot),
    ]
    
    for name, func in base_sources:
        test_news_source(name, func)
    
    # 测试分类函数
    print("\n📊 测试分类函数")
    print("-" * 40)
    
    categories = [
        ("国内要闻", fetch_domestic_news),
        ("经济财经", fetch_economy_news),
        ("军事国防", fetch_military_news),
        ("科技前沿", fetch_tech_news),
        ("社会民生", fetch_society_news),
    ]
    
    for name, func in categories:
        test_news_source(name, func)

if __name__ == "__main__":
    main()
