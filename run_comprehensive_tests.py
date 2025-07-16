#!/usr/bin/env python3
"""
综合测试执行脚本
使用llm_test_cases.json中的测试用例进行全面测试
"""

import sys
import json
import asyncio
import time
import random
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from handlers.llm_handler import LLMAnalysisHandler
from models.schemas import IntentType, AnalysisContext, AnalysisResult

class ComprehensiveTestRunner:
    """综合测试运行器"""
    
    def __init__(self, config_file: str = "llm_test_cases.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.llm_handler = LLMAnalysisHandler(use_llm=False)
        self.test_results = []
        self.start_time = None
        
    def load_config(self) -> Dict[str, Any]:
        """加载测试配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return {}
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始综合测试执行")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # 运行基础测试用例
        await self.run_basic_test_cases()
        
        # 运行LLM特定测试
        await self.run_llm_specific_tests()
        
        # 运行动态生成的测试
        await self.run_dynamic_tests()
        
        # 生成报告
        self.generate_comprehensive_report()
    
    async def run_basic_test_cases(self):
        """运行基础测试用例"""
        print("\n📋 运行基础测试用例...")
        
        test_cases = self.config.get('test_cases', [])
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"🧪 [{i}/{len(test_cases)}] {test_case['name']}")
            
            try:
                result = await self.execute_test_case(test_case)
                self.test_results.append(result)
                
                # 显示简要结果
                status = "✅" if result['success'] else "❌"
                score = result.get('score', 0)
                print(f"   {status} 得分: {score:.1f}/10")
                
                # 延迟避免过载
                if self.config.get('test_configuration', {}).get('delay_between_tests', 0) > 0:
                    await asyncio.sleep(self.config['test_configuration']['delay_between_tests'])
                    
            except Exception as e:
                print(f"   ❌ 测试执行失败: {e}")
                self.test_results.append({
                    'test_id': test_case['id'],
                    'success': False,
                    'error': str(e),
                    'score': 0
                })
    
    async def run_llm_specific_tests(self):
        """运行LLM特定测试"""
        print("\n🧠 运行LLM特定测试...")
        
        llm_tests = self.config.get('llm_specific_tests', [])
        
        for i, test_case in enumerate(llm_tests, 1):
            print(f"🔬 [{i}/{len(llm_tests)}] {test_case['name']}")
            
            try:
                result = await self.execute_llm_test(test_case)
                self.test_results.append(result)
                
                status = "✅" if result['success'] else "❌"
                print(f"   {status} {result.get('summary', '完成')}")
                
            except Exception as e:
                print(f"   ❌ LLM测试失败: {e}")
    
    async def run_dynamic_tests(self):
        """运行动态生成的测试"""
        print("\n🎲 运行动态生成测试...")
        
        test_data = self.config.get('test_data', {})
        stock_codes = test_data.get('sample_stock_codes', [])
        queries = test_data.get('sample_queries', [])
        
        # 生成随机测试组合
        for i in range(10):  # 生成10个随机测试
            stock_code = random.choice(stock_codes)
            query_template = random.choice(queries)
            query = query_template.format(stock_code=stock_code)
            
            print(f"🎯 [动态{i+1}] {query}")
            
            try:
                result = await self.llm_handler.analyze_query(query, "test_user")
                
                # 简单评估
                score = self.evaluate_dynamic_result(result, query)
                
                self.test_results.append({
                    'test_id': f'dynamic_{i+1}',
                    'query': query,
                    'success': True,
                    'score': score,
                    'type': 'dynamic'
                })
                
                print(f"   ✅ 得分: {score:.1f}/10")
                
            except Exception as e:
                print(f"   ❌ 动态测试失败: {e}")
    
    async def execute_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个测试用例"""
        start_time = time.time()
        
        try:
            # 执行查询
            result = await self.llm_handler.analyze_query(test_case['prompt'], "test_user")
            execution_time = time.time() - start_time
            
            # 评估结果
            score = self.evaluate_result(test_case, result, execution_time)
            
            return {
                'test_id': test_case['id'],
                'name': test_case['name'],
                'category': test_case.get('category', 'unknown'),
                'priority': test_case.get('priority', 'medium'),
                'query': test_case['prompt'],
                'success': True,
                'score': score,
                'execution_time': execution_time,
                'result_summary': result.summary,
                'insights_count': len(result.insights),
                'recommendations_count': len(result.recommendations),
                'confidence': result.confidence,
                'risk_level': result.risk_level
            }
            
        except Exception as e:
            return {
                'test_id': test_case['id'],
                'name': test_case['name'],
                'success': False,
                'error': str(e),
                'score': 0,
                'execution_time': time.time() - start_time
            }
    
    async def execute_llm_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """执行LLM特定测试"""
        try:
            result = await self.llm_handler.analyze_query(test_case['prompt'], "test_user")
            
            # 根据测试类型进行特定验证
            validation_result = self.validate_llm_test(test_case, result)
            
            return {
                'test_id': test_case['id'],
                'name': test_case['name'],
                'test_type': test_case.get('test_type', 'unknown'),
                'success': validation_result['success'],
                'summary': validation_result['summary'],
                'details': validation_result.get('details', {})
            }
            
        except Exception as e:
            return {
                'test_id': test_case['id'],
                'success': False,
                'error': str(e)
            }
    
    def evaluate_result(self, test_case: Dict[str, Any], result: AnalysisResult, execution_time: float) -> float:
        """评估测试结果"""
        score = 0.0
        max_score = 10.0
        
        # 1. 基础完整性 (3分)
        if result.summary and len(result.summary) > 10:
            score += 1.0
        if len(result.insights) > 0:
            score += 1.0
        if len(result.recommendations) > 0:
            score += 1.0
        
        # 2. 置信度合理性 (2分)
        if 0.3 <= result.confidence <= 1.0:
            score += 2.0
        elif 0.0 <= result.confidence < 0.3:
            score += 1.0
        
        # 3. 响应时间 (2分)
        if execution_time < 3.0:
            score += 2.0
        elif execution_time < 10.0:
            score += 1.0
        
        # 4. 内容质量 (2分)
        content_quality = self.assess_content_quality(result, test_case)
        score += content_quality
        
        # 5. 风险评估 (1分)
        if result.risk_level in ["低风险", "中等风险", "高风险", "未知"]:
            score += 1.0
        
        return min(score, max_score)
    
    def assess_content_quality(self, result: AnalysisResult, test_case: Dict[str, Any]) -> float:
        """评估内容质量"""
        quality_score = 0.0
        
        # 检查关键词覆盖
        expected_keywords = test_case.get('expected_entities', [])
        content_text = f"{result.summary} {' '.join(result.insights)} {' '.join(result.recommendations)}".lower()
        
        if expected_keywords:
            keyword_coverage = sum(1 for keyword in expected_keywords 
                                 if keyword.lower() in content_text) / len(expected_keywords)
            quality_score += keyword_coverage * 1.0
        else:
            quality_score += 1.0
        
        # 检查内容长度和详细程度
        total_content_length = len(result.summary) + sum(len(insight) for insight in result.insights)
        if total_content_length > 100:
            quality_score += 1.0
        elif total_content_length > 50:
            quality_score += 0.5
        
        return min(quality_score, 2.0)
    
    def evaluate_dynamic_result(self, result: AnalysisResult, query: str) -> float:
        """评估动态测试结果"""
        score = 0.0
        
        # 基础检查
        if result.summary:
            score += 3.0
        if len(result.insights) > 0:
            score += 2.0
        if len(result.recommendations) > 0:
            score += 2.0
        if result.confidence > 0.0:
            score += 2.0
        if result.risk_level != "未知":
            score += 1.0
        
        return min(score, 10.0)
    
    def validate_llm_test(self, test_case: Dict[str, Any], result: AnalysisResult) -> Dict[str, Any]:
        """验证LLM特定测试"""
        test_type = test_case.get('test_type', 'unknown')
        
        if test_type == 'tool_calling':
            return self.validate_tool_calling(test_case, result)
        elif test_type == 'data_analysis':
            return self.validate_data_analysis(test_case, result)
        elif test_type == 'reasoning':
            return self.validate_reasoning(test_case, result)
        elif test_type == 'error_handling':
            return self.validate_error_handling(test_case, result)
        else:
            return {'success': True, 'summary': '基础验证通过'}
    
    def validate_tool_calling(self, test_case: Dict[str, Any], result: AnalysisResult) -> Dict[str, Any]:
        """验证工具调用"""
        # 更全面的工具调用检测
        indicators = []

        # 检查数据点
        if len(result.data_points) > 0:
            indicators.append("有数据点")

        # 检查洞察数量
        if len(result.insights) > 0:
            indicators.append("有分析洞察")

        # 检查建议数量
        if len(result.recommendations) > 0:
            indicators.append("有投资建议")

        # 检查置信度
        if result.confidence > 0.5:
            indicators.append("置信度较高")

        # 检查摘要内容
        if result.summary and len(result.summary) > 20:
            indicators.append("有详细摘要")

        # 检查是否有具体的股票代码识别
        if any(code in result.summary for code in ['000001', '600519', '000002']):
            indicators.append("识别到股票代码")

        success = len(indicators) >= 3  # 至少满足3个指标

        return {
            'success': success,
            'summary': f'工具调用验证{"通过" if success else "失败"} - 满足{len(indicators)}个指标',
            'details': {'indicators': indicators}
        }
    
    def validate_data_analysis(self, test_case: Dict[str, Any], result: AnalysisResult) -> Dict[str, Any]:
        """验证数据分析"""
        analysis_quality = []

        # 检查洞察质量
        if len(result.insights) >= 2:
            analysis_quality.append("洞察数量充足")
        elif len(result.insights) >= 1:
            analysis_quality.append("有基础洞察")

        # 检查数据点
        if len(result.data_points) > 0:
            analysis_quality.append("有数据支撑")

        # 检查分析深度
        total_content = len(result.summary) + sum(len(insight) for insight in result.insights)
        if total_content > 200:
            analysis_quality.append("分析内容详细")
        elif total_content > 100:
            analysis_quality.append("分析内容适中")

        # 检查专业性
        professional_terms = ['PE', 'PB', 'ROE', '市盈率', '估值', '基本面', '技术面', '风险']
        content_text = f"{result.summary} {' '.join(result.insights)}".lower()
        if any(term.lower() in content_text for term in professional_terms):
            analysis_quality.append("包含专业术语")

        success = len(analysis_quality) >= 2

        return {
            'success': success,
            'summary': f'数据分析验证{"通过" if success else "不充分"} - {len(analysis_quality)}个质量指标',
            'details': {'quality_indicators': analysis_quality}
        }
    
    def validate_reasoning(self, test_case: Dict[str, Any], result: AnalysisResult) -> Dict[str, Any]:
        """验证推理能力"""
        has_reasoning = len(result.recommendations) > 0 and result.confidence > 0.5
        
        return {
            'success': has_reasoning,
            'summary': '推理验证通过' if has_reasoning else '推理能力不足'
        }
    
    def validate_error_handling(self, test_case: Dict[str, Any], result: AnalysisResult) -> Dict[str, Any]:
        """验证错误处理"""
        # 错误处理测试应该有合理的响应，即使数据获取失败
        has_graceful_handling = result.summary and "错误" not in result.summary.lower()
        
        return {
            'success': has_graceful_handling,
            'summary': '错误处理验证通过' if has_graceful_handling else '错误处理需要改进'
        }
    
    def generate_comprehensive_report(self):
        """生成综合报告"""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("📊 综合测试报告")
        print("=" * 80)
        
        # 总体统计
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get('success', False))
        average_score = sum(r.get('score', 0) for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        print(f"📈 总体表现:")
        print(f"   测试用例总数: {total_tests}")
        print(f"   成功执行: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"   平均得分: {average_score:.1f}/10")
        print(f"   总执行时间: {total_time:.2f}秒")
        
        # 按类别统计
        self.generate_category_stats()
        
        # 按优先级统计
        self.generate_priority_stats()
        
        # 性能分析
        self.generate_performance_analysis()
        
        # 保存详细报告
        self.save_detailed_report()
        
        # 生成改进建议
        self.generate_improvement_suggestions()
    
    def generate_category_stats(self):
        """生成分类统计"""
        print(f"\n📋 分类表现:")
        
        categories = {}
        for result in self.test_results:
            cat = result.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for category, results in categories.items():
            cat_score = sum(r.get('score', 0) for r in results) / len(results)
            cat_success = sum(1 for r in results if r.get('success', False)) / len(results) * 100
            print(f"   {category}: {cat_score:.1f}/10 (成功率: {cat_success:.1f}%)")
    
    def generate_priority_stats(self):
        """生成优先级统计"""
        print(f"\n🎯 优先级表现:")
        
        priorities = {}
        for result in self.test_results:
            pri = result.get('priority', 'medium')
            if pri not in priorities:
                priorities[pri] = []
            priorities[pri].append(result)
        
        for priority in ['high', 'medium', 'low']:
            if priority in priorities:
                results = priorities[priority]
                pri_score = sum(r.get('score', 0) for r in results) / len(results)
                pri_success = sum(1 for r in results if r.get('success', False)) / len(results) * 100
                print(f"   {priority}: {pri_score:.1f}/10 (成功率: {pri_success:.1f}%)")
    
    def generate_performance_analysis(self):
        """生成性能分析"""
        print(f"\n⚡ 性能分析:")
        
        execution_times = [r.get('execution_time', 0) for r in self.test_results if r.get('execution_time')]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)
            
            print(f"   平均响应时间: {avg_time:.2f}秒")
            print(f"   最快响应: {min_time:.2f}秒")
            print(f"   最慢响应: {max_time:.2f}秒")
    
    def generate_improvement_suggestions(self):
        """生成改进建议"""
        print(f"\n💡 改进建议:")
        
        # 分析失败的测试
        failed_tests = [r for r in self.test_results if not r.get('success', False)]
        if failed_tests:
            print(f"   🔧 {len(failed_tests)} 个测试失败，需要修复错误处理")
        
        # 分析低分测试
        low_score_tests = [r for r in self.test_results if r.get('score', 0) < 5.0]
        if low_score_tests:
            print(f"   📈 {len(low_score_tests)} 个测试得分较低，需要改进算法")
        
        # 分析性能问题
        slow_tests = [r for r in self.test_results if r.get('execution_time', 0) > 10.0]
        if slow_tests:
            print(f"   ⚡ {len(slow_tests)} 个测试响应较慢，需要优化性能")
    
    def save_detailed_report(self):
        """保存详细报告"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.test_results),
                "successful_tests": sum(1 for r in self.test_results if r.get('success', False)),
                "average_score": sum(r.get('score', 0) for r in self.test_results) / len(self.test_results),
                "total_execution_time": time.time() - self.start_time
            },
            "detailed_results": self.test_results,
            "configuration": self.config
        }
        
        with open("comprehensive_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 详细报告已保存到: comprehensive_test_report.json")

async def main():
    """主函数"""
    runner = ComprehensiveTestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
