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
    
    def run_zero_shot(self, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        运行Zero-shot baseline
        
        Args:
            test_data: 测试数据
            
        Returns:
            List[Dict]: 结果列表
        """
        print("\n🚀 开始Zero-shot baseline...")
        results = []
        
        for i, item in enumerate(test_data):
            if config.VERBOSE:
                print(f"处理问题 {i+1}/{len(test_data)}: {item['question'][:50]}...")
            
            # 构建zero-shot prompt
            messages = nshot_chats(n=0, question=item['question'])
            
            try:
                # 调用API
                response, token_stats = self.client.generate_response(messages)
                token_tracker.add_usage(token_stats)
                
                # 提取答案
                predicted_answer = extract_ans_from_response(response)
                ground_truth = extract_ans_from_response(item['answer'])
                
                # 保存结果
                result = {
                    'question': item['question'],
                    'ground_truth': ground_truth,
                    'predicted_answer': predicted_answer,
                    'response': response,
                    'token_stats': token_stats,
                    'correct': predicted_answer == ground_truth
                }
                results.append(result)
                
                if config.VERBOSE:
                    print(f"  预测答案: {predicted_answer}, 正确答案: {ground_truth}, 正确: {result['correct']}")
                    
            except Exception as e:
                print(f"❌ 处理问题 {i+1} 时出错: {e}")
                results.append({
                    'question': item['question'],
                    'ground_truth': extract_ans_from_response(item['answer']),
                    'predicted_answer': None,
                    'response': None,
                    'token_stats': None,
                    'correct': False,
                    'error': str(e)
                })
        
        print(f"✅ Zero-shot baseline完成，处理了 {len(results)} 个问题")
        return results
    
    def run_few_shot(self, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        运行Few-shot baseline
        
        Args:
            test_data: 测试数据
            
        Returns:
            List[Dict]: 结果列表
        """
        print("\n🚀 开始Few-shot baseline...")
        results = []
        
        for i, item in enumerate(test_data):
            if config.VERBOSE:
                print(f"处理问题 {i+1}/{len(test_data)}: {item['question'][:50]}...")
            
            # 构建few-shot prompt (使用8个示例)
            messages = nshot_chats(n=8, question=item['question'])
            
            try:
                # 调用API
                response, token_stats = self.client.generate_response(messages)
                token_tracker.add_usage(token_stats)
                
                # 提取答案
                predicted_answer = extract_ans_from_response(response)
                ground_truth = extract_ans_from_response(item['answer'])
                
                # 保存结果
                result = {
                    'question': item['question'],
                    'ground_truth': ground_truth,
                    'predicted_answer': predicted_answer,
                    'response': response,
                    'token_stats': token_stats,
                    'correct': predicted_answer == ground_truth
                }
                results.append(result)
                
                if config.VERBOSE:
                    print(f"  预测答案: {predicted_answer}, 正确答案: {ground_truth}, 正确: {result['correct']}")
                    
            except Exception as e:
                print(f"❌ 处理问题 {i+1} 时出错: {e}")
                results.append({
                    'question': item['question'],
                    'ground_truth': extract_ans_from_response(item['answer']),
                    'predicted_answer': None,
                    'response': None,
                    'token_stats': None,
                    'correct': False,
                    'error': str(e)
                })
        
        print(f"✅ Few-shot baseline完成，处理了 {len(results)} 个问题")
        return results
    
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
        
        # 创建并发处理器
        processor = ConcurrentProcessor(max_concurrent=10, rate_limit=100)
        
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

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GSM8K Baseline Runner')
    parser.add_argument('--test-file', default=config.TEST_FILE, help='测试文件路径')
    parser.add_argument('--output-dir', default=config.OUTPUT_DIR, help='输出目录')
    parser.add_argument('--max-questions', type=int, default=None, help='最大处理问题数量')
    parser.add_argument('--method', choices=['zero-shot', 'few-shot', 'concurrent', 'all'], default='both', help='运行的方法')
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
        zero_shot_results = runner.run_zero_shot(test_data)
        runner.save_results(zero_shot_results, 'zeroshot.baseline.jsonl')
        
        accuracy = runner.calculate_accuracy(zero_shot_results)
        print(f"📊 Zero-shot 准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    if args.method in ['few-shot', 'both', 'all']:
        few_shot_results = runner.run_few_shot(test_data)
        runner.save_results(few_shot_results, 'fewshot.baseline.jsonl')
        
        accuracy = runner.calculate_accuracy(few_shot_results)
        print(f"📊 Few-shot 准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    
    if args.method in ['concurrent', 'all']:
        print("🚀 开始并发处理...")
        concurrent_results = asyncio.run(runner.run_concurrent_baseline(test_data, "zero-shot"))
        runner.save_results(concurrent_results, 'concurrent.baseline.jsonl')
        
        accuracy = runner.calculate_accuracy(concurrent_results)
        print(f"📊 并发Zero-shot 准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    # 打印token使用统计
    token_tracker.print_summary()
    
    print("\n🎉 Baseline执行完成！")

if __name__ == "__main__":
    main()
