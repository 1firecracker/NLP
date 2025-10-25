"""
GSM8K Baseline 主执行脚本
"""
import os
import sys
import json
import argparse
import time
import asyncio
from typing import List, Dict, Any
from pathlib import Path

# 导入项目模块
from data.config import config
from core.llm_client import LLMClient, token_tracker
from core.baseline import nshot_chats
from core.evaluation import extract_ans_from_response
from processing.concurrent_processor import ConcurrentProcessor
from analysis.method_comparator import MethodComparator, MethodResult

class BaselineRunner:
    """Baseline执行器"""
    
    def __init__(self):
        """初始化执行器"""
        self.client = LLMClient()
        self.results = []
        
    def load_test_data(self, file_path: str) -> List[Dict[str, Any]]:
        """
        加载测试数据
        
        Args:
            file_path: 测试文件路径
            
        Returns:
            List[Dict]: 测试数据列表
        """
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line.strip()))
            print(f"✅ 成功加载 {len(data)} 条测试数据")
            return data
        except FileNotFoundError:
            print(f"❌ 测试文件不存在: {file_path}")
            return []
        except Exception as e:
            print(f"❌ 加载测试数据失败: {e}")
            return []
    
    async def run_zero_shot(self, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """运行Zero-shot baseline（使用并发处理）"""
        print(f"\n🚀 开始Zero-shot baseline...")
        
        # 创建并发处理器
        processor = ConcurrentProcessor(max_concurrent=5, rate_limit=100)
        
        # 并发处理
        results = await processor.process_batch(test_data, method="zero-shot")
        
        # 转换为标准格式
        standard_results = []
        for result in results:
            standard_results.append({
                'question': result.question,
                'ground_truth': result.ground_truth,
                'predicted_answer': result.predicted_answer,
                'response': result.response,
                'token_stats': result.token_stats,
                'correct': result.correct,
                'processing_time': result.processing_time,
                'error': result.error
            })
        
        print(f"✅ Zero-shot baseline完成，处理了 {len(standard_results)} 个问题")
        return standard_results
    
    async def run_few_shot(self, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """运行Few-shot baseline（使用并发处理）"""
        print(f"\n🚀 开始Few-shot baseline...")
        
        # 创建并发处理器
        processor = ConcurrentProcessor(max_concurrent=5, rate_limit=100)
        
        # 并发处理
        results = await processor.process_batch(test_data, method="few-shot")
        
        # 转换为标准格式
        standard_results = []
        for result in results:
            standard_results.append({
                'question': result.question,
                'ground_truth': result.ground_truth,
                'predicted_answer': result.predicted_answer,
                'response': result.response,
                'token_stats': result.token_stats,
                'correct': result.correct,
                'processing_time': result.processing_time,
                'error': result.error
            })
        
        print(f"✅ Few-shot baseline完成，处理了 {len(standard_results)} 个问题")
        return standard_results
    
    async def run_concurrent_baseline(self, test_data: List[Dict[str, Any]], method: str = "zero-shot") -> List[Dict[str, Any]]:
        """
        运行并发baseline
        
        Args:
            test_data: 测试数据
            method: 处理方法
            
        Returns:
            List[Dict]: 结果列表
        """
        print(f"\n🚀 开始并发{method} baseline...")
        
        # 创建并发处理器（优化速率限制）
        processor = ConcurrentProcessor(max_concurrent=5, rate_limit=100)
        
        # 并发处理
        results = await processor.process_batch(test_data, method=method)
        
        # 转换为标准格式
        standard_results = []
        for result in results:
            standard_results.append({
                'question': result.question,
                'ground_truth': result.ground_truth,
                'predicted_answer': result.predicted_answer,
                'response': result.response,
                'token_stats': result.token_stats,
                'correct': result.correct,
                'processing_time': result.processing_time,
                'error': result.error
            })
        
        print(f"✅ 并发{method} baseline完成，处理了 {len(standard_results)} 个问题")
        return standard_results
    
    async def run_progressive_hint(self, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """运行Progressive-Hint baseline（使用并发处理）"""
        print(f"\n🚀 开始Progressive-Hint baseline...")
        
        # 创建并发处理器
        processor = ConcurrentProcessor(max_concurrent=5, rate_limit=100)
        
        # 并发处理
        results = await processor.process_batch(test_data, method="progressive-hint")
        
        # 转换为标准格式
        standard_results = []
        for result in results:
            standard_results.append({
                'question': result.question,
                'ground_truth': result.ground_truth,
                'predicted_answer': result.predicted_answer,
                'response': result.response,
                'token_stats': result.token_stats,
                'correct': result.correct,
                'processing_time': result.processing_time,
                'error': result.error
            })
        
        print(f"✅ Progressive-Hint baseline完成，处理了 {len(standard_results)} 个问题")
        return standard_results
    
    async def run_program_of_thoughts(self, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """运行Program of Thoughts baseline（使用并发处理）"""
        print(f"\n🚀 开始Program of Thoughts baseline...")
        
        # 创建并发处理器（优化速率限制）
        processor = ConcurrentProcessor(max_concurrent=5, rate_limit=100)
        
        # 并发处理
        results = await processor.process_batch(test_data, method="program-of-thoughts")
        
        # 转换为标准格式
        standard_results = []
        for result in results:
            standard_results.append({
                'question': result.question,
                'ground_truth': result.ground_truth,
                'predicted_answer': result.predicted_answer,
                'response': result.response,
                'token_stats': result.token_stats,
                'correct': result.correct,
                'processing_time': result.processing_time,
                'error': result.error
            })
        
        print(f"✅ Program of Thoughts baseline完成，处理了 {len(standard_results)} 个问题")
        return standard_results
    
    async def run_hybrid_pot_php(self, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """运行混合PoT和PHP baseline（使用并发处理）"""
        print(f"\n🚀 开始混合PoT和PHP baseline...")
        
        # 创建并发处理器
        processor = ConcurrentProcessor(max_concurrent=5, rate_limit=100)
        
        # 并发处理
        results = await processor.process_batch(test_data, method="hybrid-pot-php")
        
        # 转换为标准格式
        standard_results = []
        for result in results:
            standard_results.append({
                'question': result.question,
                'ground_truth': result.ground_truth,
                'predicted_answer': result.predicted_answer,
                'response': result.response,
                'token_stats': result.token_stats,
                'correct': result.correct,
                'processing_time': result.processing_time,
                'error': result.error
            })
        
        print(f"✅ 混合PoT和PHP baseline完成，处理了 {len(standard_results)} 个问题")
        return standard_results
    
    def save_results(self, results: List[Dict[str, Any]], filename: str):
        """
        保存结果到文件
        
        Args:
            results: 结果列表
            filename: 输出文件名
        """
        # 确保输出目录存在
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        file_path = os.path.join(config.OUTPUT_DIR, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
            print(f"✅ 结果已保存到: {file_path}")
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")
    
    def calculate_accuracy(self, results: List[Dict[str, Any]]) -> float:
        """
        计算准确率
        
        Args:
            results: 结果列表
            
        Returns:
            float: 准确率
        """
        correct_count = sum(1 for result in results if result.get('correct', False))
        total_count = len(results)
        accuracy = correct_count / total_count if total_count > 0 else 0.0
        return accuracy
    
    def generate_analysis_report(self, results: List[Dict[str, Any]], method_name: str, 
                                processing_time: float = 0.0) -> Dict[str, Any]:
        """
        生成单次结果分析报告
        
        Args:
            results: 结果列表
            method_name: 方法名称
            processing_time: 处理时间
            
        Returns:
            Dict: 分析报告
        """
        if not results:
            return {}
        
        # 基础统计
        total_questions = len(results)
        correct_answers = sum(1 for r in results if r.get('correct', False))
        accuracy = correct_answers / total_questions if total_questions > 0 else 0.0
        
        # Token统计
        total_input_tokens = sum(r.get('token_stats', {}).get('prompt_tokens', 0) for r in results)
        total_output_tokens = sum(r.get('token_stats', {}).get('completion_tokens', 0) for r in results)
        total_tokens = total_input_tokens + total_output_tokens
        avg_tokens_per_question = total_tokens / total_questions if total_questions > 0 else 0.0
        
        # 时间统计
        avg_processing_time = processing_time / total_questions if total_questions > 0 else 0.0
        
        # 成本分析 (假设价格，可根据实际API调整)
        input_token_cost_per_k = 0.0005  # $0.5 per 1K tokens
        output_token_cost_per_k = 0.0015  # $1.5 per 1K tokens
        estimated_cost = (total_input_tokens / 1000 * input_token_cost_per_k) + \
                        (total_output_tokens / 1000 * output_token_cost_per_k)
        
        # 错误分析
        error_count = sum(1 for r in results if r.get('error'))
        error_rate = error_count / total_questions if total_questions > 0 else 0.0
        
        # 生成报告
        report = {
            "method_name": method_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "hyperparameters": {
                "temperature": config.TEMPERATURE,
                "top_p": config.TOP_P,
                "max_tokens": config.MAX_TOKENS,
                "frequency_penalty": config.FREQUENCY_PENALTY,
                "presence_penalty": config.PRESENCE_PENALTY
            },
            "performance_metrics": {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "accuracy": accuracy,
                "wall_clock_time": processing_time,
                "avg_processing_time_per_question": avg_processing_time
            },
            "token_usage": {
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tokens": total_tokens,
                "avg_tokens_per_question": avg_tokens_per_question
            },
            "cost_analysis": {
                "estimated_cost_usd": estimated_cost,
                "cost_per_question": estimated_cost / total_questions if total_questions > 0 else 0.0
            },
            "error_analysis": {
                "error_count": error_count,
                "error_rate": error_rate
            }
        }
        
        return report
    
    def save_analysis_report(self, report: Dict[str, Any], method_name: str):
        """
        保存分析报告到文件
        
        Args:
            report: 分析报告
            method_name: 方法名称
        """
        # 生成文件名: 方法名_温度_top-p_时间戳
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        temp_str = f"{config.TEMPERATURE:.1f}".replace('.', 'p')
        top_p_str = f"{config.TOP_P:.1f}".replace('.', 'p')
        
        filename = f"{method_name}_temp{temp_str}_topp{top_p_str}_{timestamp}.json"
        filepath = os.path.join(config.SUMMARY_DIR, filename)
        
        # 确保目录存在
        os.makedirs(config.SUMMARY_DIR, exist_ok=True)
        
        # 保存报告
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 分析报告已保存到: {filepath}")
        
        # 打印简要统计
        metrics = report['performance_metrics']
        token_usage = report['token_usage']
        cost_analysis = report['cost_analysis']
        
        print(f"📈 {method_name} 分析结果:")
        print(f"   - 准确率: {metrics['accuracy']:.2%}")
        print(f"   - 处理时间: {metrics['wall_clock_time']:.2f}秒")
        print(f"   - 平均时间/问题: {metrics['avg_processing_time_per_question']:.2f}秒")
        print(f"   - 平均Token/问题: {token_usage['avg_tokens_per_question']:.1f}")
        print(f"   - 预估成本: ${cost_analysis['estimated_cost_usd']:.4f}")
        print(f"   - 超参数: temp={config.TEMPERATURE}, top_p={config.TOP_P}")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GSM8K Baseline Runner')
    parser.add_argument('--test-file', default=config.TEST_FILE, help='测试文件路径')
    parser.add_argument('--output-dir', default=config.OUTPUT_DIR, help='输出目录')
    parser.add_argument('--max-questions', type=int, default=None, help='最大处理问题数量')
    parser.add_argument('--method', choices=['zero-shot', 'few-shot', 'concurrent', 'progressive-hint', 'program-of-thoughts', 'hybrid-pot-php', 'all'], default='both', help='运行的方法')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 更新配置
    config.TEST_FILE = args.test_file
    config.OUTPUT_DIR = args.output_dir
    config.VERBOSE = args.verbose
    
    print("🎯 GSM8K Baseline 开始执行")
    print("=" * 50)
    
    # 验证配置
    if not config.validate():
        print("❌ 配置验证失败，请检查API密钥设置")
        return
    
    # 打印配置
    config.print_config()
    
    # 测试API连接
    runner = BaselineRunner()
    if not runner.client.test_connection():
        print("❌ API连接测试失败，请检查网络和API密钥")
        return
    
    # 加载测试数据
    test_data = runner.load_test_data(config.TEST_FILE)
    if not test_data:
        print("❌ 无法加载测试数据")
        return
    
    # 限制处理数量（用于测试）
    if args.max_questions:
        test_data = test_data[:args.max_questions]
        print(f"🔬 测试模式：仅处理前 {len(test_data)} 个问题")
    
    # 运行baseline
    if args.method in ['zero-shot', 'both', 'all']:
        start_time = time.time()
        zero_shot_results = await runner.run_zero_shot(test_data)
        processing_time = time.time() - start_time
        
        runner.save_results(zero_shot_results, 'zeroshot.baseline.jsonl')
        
        accuracy = runner.calculate_accuracy(zero_shot_results)
        print(f"📊 Zero-shot 准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        # 生成分析报告
        report = runner.generate_analysis_report(zero_shot_results, "zero-shot", processing_time)
        runner.save_analysis_report(report, "zero-shot")
    
    if args.method in ['few-shot', 'both', 'all']:
        start_time = time.time()
        few_shot_results = await runner.run_few_shot(test_data)
        processing_time = time.time() - start_time
        
        runner.save_results(few_shot_results, 'fewshot.baseline.jsonl')
        
        accuracy = runner.calculate_accuracy(few_shot_results)
        print(f"📊 Few-shot 准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        # 生成分析报告
        report = runner.generate_analysis_report(few_shot_results, "few-shot", processing_time)
        runner.save_analysis_report(report, "few-shot")
    
    if args.method in ['concurrent', 'all']:
        print("🚀 开始并发处理...")
        start_time = time.time()
        concurrent_results = asyncio.run(runner.run_concurrent_baseline(test_data, "zero-shot"))
        processing_time = time.time() - start_time
        
        runner.save_results(concurrent_results, 'concurrent.baseline.jsonl')
        
        accuracy = runner.calculate_accuracy(concurrent_results)
        print(f"📊 并发Zero-shot 准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        # 生成分析报告
        report = runner.generate_analysis_report(concurrent_results, "concurrent", processing_time)
        runner.save_analysis_report(report, "concurrent")
    
    if args.method in ['progressive-hint', 'all']:
        start_time = time.time()
        progressive_hint_results = await runner.run_progressive_hint(test_data)
        processing_time = time.time() - start_time
        
        runner.save_results(progressive_hint_results, 'progressive_hint.baseline.jsonl')
        
        accuracy = runner.calculate_accuracy(progressive_hint_results)
        print(f"📊 Progressive-Hint 准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        # 生成分析报告
        report = runner.generate_analysis_report(progressive_hint_results, "progressive-hint", processing_time)
        runner.save_analysis_report(report, "progressive-hint")
    
    if args.method in ['program-of-thoughts', 'all']:
        start_time = time.time()
        pot_results = await runner.run_program_of_thoughts(test_data)
        processing_time = time.time() - start_time
        
        runner.save_results(pot_results, 'program_of_thoughts.baseline.jsonl')
        
        accuracy = runner.calculate_accuracy(pot_results)
        print(f"📊 Program of Thoughts 准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        # 生成分析报告
        report = runner.generate_analysis_report(pot_results, "program-of-thoughts", processing_time)
        runner.save_analysis_report(report, "program-of-thoughts")
    
    if args.method in ['hybrid-pot-php', 'all']:
        start_time = time.time()
        hybrid_results = await runner.run_hybrid_pot_php(test_data)
        processing_time = time.time() - start_time
        
        runner.save_results(hybrid_results, 'hybrid_pot_php.baseline.jsonl')
        
        accuracy = runner.calculate_accuracy(hybrid_results)
        print(f"📊 混合PoT和PHP 准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        # 生成分析报告
        report = runner.generate_analysis_report(hybrid_results, "hybrid-pot-php", processing_time)
        runner.save_analysis_report(report, "hybrid-pot-php")
    
    # 打印token使用统计
    token_tracker.print_summary()
    
    print("\n🎉 Baseline执行完成！")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
