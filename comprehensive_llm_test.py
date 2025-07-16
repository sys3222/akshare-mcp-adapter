#!/usr/bin/env python3
"""
LLM系统综合测试框架
系统化测试LLM回答效果和质量
"""

import sys
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from handlers.llm_handler import LLMAnalysisHandler
from models.schemas import IntentType, AnalysisContext, AnalysisResult

class LLMTestFramework:
    """LLM测试框架"""
    
    def __init__(self):
        self.llm_handler = LLMAnalysisHandler(use_llm=False)  # 先测试规则模式
        self.test_results = []
        self.performance_metrics = {}
        
    def create_test_cases(self) -> List[Dict[str, Any]]:
        """创建测试用例"""
        return [
            # 基础股票分析测试
            {
                "id": "stock_basic_001",
                "category": "股票分析",
                "query": "分析000001平安银行",
                "expected_intent": IntentType.STOCK_ANALYSIS,
                "expected_keywords": ["平安银行", "000001", "股价", "分析"],
                "quality_criteria": {
                    "min_insights": 1,
                    "min_recommendations": 1,
                    "min_confidence": 0.7
                }
            },
            {
                "id": "stock_basic_002", 
                "category": "股票分析",
                "query": "000001怎么样？值得投资吗？",
                "expected_intent": IntentType.STOCK_ANALYSIS,
                "expected_keywords": ["投资", "建议", "风险"],
                "quality_criteria": {
                    "min_insights": 1,
                    "min_recommendations": 2,
                    "min_confidence": 0.6
                }
            },
            
            # 市场概览测试
            {
                "id": "market_001",
                "category": "市场概览", 
                "query": "今日A股市场表现如何？",
                "expected_intent": IntentType.MARKET_OVERVIEW,
                "expected_keywords": ["A股", "市场", "表现"],
                "quality_criteria": {
                    "min_insights": 1,
                    "min_confidence": 0.5
                }
            },
            {
                "id": "market_002",
                "category": "市场概览",
                "query": "整体市场走势怎么样？",
                "expected_intent": IntentType.MARKET_OVERVIEW,
                "expected_keywords": ["市场", "走势", "整体"],
                "quality_criteria": {
                    "min_insights": 1,
                    "min_confidence": 0.5
                }
            },
            
            # 财务指标测试
            {
                "id": "financial_001",
                "category": "财务指标",
                "query": "000001的PE和ROE怎么样？",
                "expected_intent": IntentType.FINANCIAL_METRICS,
                "expected_keywords": ["PE", "ROE", "财务", "指标"],
                "quality_criteria": {
                    "min_insights": 1,
                    "min_confidence": 0.6
                }
            },
            
            # 复杂查询测试
            {
                "id": "complex_001",
                "category": "复杂查询",
                "query": "帮我对比分析000001和600519，哪个更值得投资？",
                "expected_intent": IntentType.COMPARISON_ANALYSIS,
                "expected_keywords": ["对比", "000001", "600519", "投资"],
                "quality_criteria": {
                    "min_insights": 2,
                    "min_recommendations": 2,
                    "min_confidence": 0.7
                }
            },
            
            # 边界情况测试
            {
                "id": "edge_001",
                "category": "边界情况",
                "query": "随机文本测试",
                "expected_intent": IntentType.UNKNOWN,
                "expected_keywords": [],
                "quality_criteria": {
                    "min_confidence": 0.0,
                    "max_confidence": 0.5
                }
            },
            {
                "id": "edge_002",
                "category": "边界情况", 
                "query": "",
                "expected_intent": IntentType.UNKNOWN,
                "expected_keywords": [],
                "quality_criteria": {
                    "min_confidence": 0.0,
                    "max_confidence": 0.3
                }
            }
        ]
    
    async def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试用例"""
        print(f"🧪 测试 {test_case['id']}: {test_case['query'][:50]}...")
        
        start_time = time.time()
        
        try:
            # 执行分析
            result = await self.llm_handler.analyze_query(test_case['query'], "test_user")
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 评估结果
            evaluation = self.evaluate_result(test_case, result, execution_time)
            
            print(f"   ✅ 完成 - 得分: {evaluation['score']:.1f}/10")
            return evaluation
            
        except Exception as e:
            print(f"   ❌ 失败: {str(e)}")
            return {
                "test_id": test_case['id'],
                "category": test_case['category'],
                "query": test_case['query'],
                "success": False,
                "error": str(e),
                "score": 0,
                "execution_time": time.time() - start_time
            }
    
    def evaluate_result(self, test_case: Dict[str, Any], result: AnalysisResult, execution_time: float) -> Dict[str, Any]:
        """评估测试结果"""
        evaluation = {
            "test_id": test_case['id'],
            "category": test_case['category'],
            "query": test_case['query'],
            "success": True,
            "execution_time": execution_time,
            "result_summary": result.summary,
            "insights_count": len(result.insights),
            "recommendations_count": len(result.recommendations),
            "confidence": result.confidence,
            "risk_level": result.risk_level
        }
        
        # 计算质量得分 (0-10分)
        score = 0
        max_score = 10
        issues = []
        
        # 1. 意图识别准确性 (2分)
        context = self.llm_handler._identify_intent(test_case['query'])
        if context.intent == test_case['expected_intent']:
            score += 2
        else:
            issues.append(f"意图识别错误: 期望{test_case['expected_intent']}, 实际{context.intent}")
        
        # 2. 置信度合理性 (2分)
        criteria = test_case['quality_criteria']
        if criteria.get('min_confidence', 0) <= result.confidence <= criteria.get('max_confidence', 1.0):
            score += 2
        else:
            issues.append(f"置信度不合理: {result.confidence}")
        
        # 3. 内容质量 (3分)
        if len(result.insights) >= criteria.get('min_insights', 0):
            score += 1.5
        else:
            issues.append(f"洞察数量不足: {len(result.insights)}")
            
        if len(result.recommendations) >= criteria.get('min_recommendations', 0):
            score += 1.5
        else:
            issues.append(f"建议数量不足: {len(result.recommendations)}")
        
        # 4. 关键词覆盖 (2分)
        content_text = f"{result.summary} {' '.join(result.insights)} {' '.join(result.recommendations)}".lower()
        keyword_coverage = sum(1 for keyword in test_case['expected_keywords'] 
                             if keyword.lower() in content_text)
        if test_case['expected_keywords']:
            keyword_score = (keyword_coverage / len(test_case['expected_keywords'])) * 2
            score += keyword_score
        else:
            score += 2  # 无关键词要求时给满分
        
        # 5. 响应时间 (1分)
        if execution_time < 5.0:
            score += 1
        elif execution_time < 10.0:
            score += 0.5
        else:
            issues.append(f"响应时间过长: {execution_time:.2f}s")
        
        evaluation.update({
            "score": min(score, max_score),
            "max_score": max_score,
            "issues": issues,
            "keyword_coverage": keyword_coverage if test_case['expected_keywords'] else "N/A"
        })
        
        return evaluation
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始LLM系统综合测试")
        print("=" * 60)
        
        test_cases = self.create_test_cases()
        
        # 运行所有测试
        for test_case in test_cases:
            result = await self.run_single_test(test_case)
            self.test_results.append(result)
            
            # 短暂延迟避免过载
            await asyncio.sleep(0.5)
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 LLM系统测试报告")
        print("=" * 60)
        
        # 总体统计
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r['success'])
        average_score = sum(r.get('score', 0) for r in self.test_results) / total_tests if total_tests > 0 else 0
        average_time = sum(r['execution_time'] for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        print(f"📈 总体表现:")
        print(f"   测试用例总数: {total_tests}")
        print(f"   成功执行: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"   平均得分: {average_score:.1f}/10")
        print(f"   平均响应时间: {average_time:.2f}秒")
        
        # 按类别统计
        print(f"\n📋 分类表现:")
        categories = {}
        for result in self.test_results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for category, results in categories.items():
            cat_score = sum(r.get('score', 0) for r in results) / len(results)
            cat_success = sum(1 for r in results if r['success']) / len(results) * 100
            print(f"   {category}: {cat_score:.1f}/10 (成功率: {cat_success:.1f}%)")
        
        # 详细结果
        print(f"\n🔍 详细测试结果:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            score_text = f"{result.get('score', 0):.1f}/10" if result['success'] else "失败"
            print(f"   {status} {result['test_id']}: {score_text}")
            
            if result['success'] and result.get('issues'):
                for issue in result['issues']:
                    print(f"      ⚠️ {issue}")
        
        # 问题总结
        all_issues = []
        for result in self.test_results:
            if result.get('issues'):
                all_issues.extend(result['issues'])
        
        if all_issues:
            print(f"\n⚠️ 发现的主要问题:")
            issue_counts = {}
            for issue in all_issues:
                issue_type = issue.split(':')[0]
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
            
            for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   {issue_type}: {count}次")
        
        # 改进建议
        print(f"\n💡 改进建议:")
        if average_score < 7:
            print("   🔧 整体表现需要改进，建议优化算法和模板")
        if average_time > 5:
            print("   ⚡ 响应时间较慢，建议优化性能")
        if successful_tests < total_tests:
            print("   🛠️ 存在执行失败的测试，需要修复错误处理")
        
        # 保存详细报告
        self.save_detailed_report()
    
    def save_detailed_report(self):
        """保存详细报告到文件"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.test_results),
                "successful_tests": sum(1 for r in self.test_results if r['success']),
                "average_score": sum(r.get('score', 0) for r in self.test_results) / len(self.test_results),
                "average_time": sum(r['execution_time'] for r in self.test_results) / len(self.test_results)
            },
            "detailed_results": self.test_results
        }
        
        with open("llm_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 详细报告已保存到: llm_test_report.json")

async def main():
    """主函数"""
    framework = LLMTestFramework()
    await framework.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
