"""
提示质量实验主脚本
"""
import os
import sys
import json
import argparse
import asyncio
import time
from typing import List, Dict, Any
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.config import config
from core.llm_client import LLMClient
from core.evaluation import extract_ans_from_response
from experiments.prompt_quality.quality_method import QualityExperimentMethod

# 实验配置
EXPERIMENTS = {
    # 维度1：演示正确性
    'baseline': {'corruption_type': None, 'description': '基线：正确演示'},
    'wrong_answer': {'corruption_type': 'wrong_answer', 'description': '错误答案演示'},
    'wrong_reasoning': {'corruption_type': 'wrong_reasoning', 'description': '错误推理步骤'},
    'completely_wrong': {'corruption_type': 'completely_wrong', 'description': '完全错误演示'},
    
    # 维度2：演示相关性
    'irrelevant': {'corruption_type': 'irrelevant', 'description': '不相关演示'},
    'partially_relevant': {'corruption_type': 'partially_relevant', 'description': '部分相关演示'},
    'mixed_50_50': {'corruption_type': 'mixed_50_50', 'description': '混合演示（50%相关）'},
    
    # 维度3：演示格式质量
    'format_inconsistent': {'corruption_type': 'format_inconsistent', 'description': '格式不一致'},
    'format_missing': {'corruption_type': 'format_missing', 'description': '缺少格式标记'},
    'format_chaotic': {'corruption_type': 'format_chaotic', 'description': '格式混乱'},
}


class QualityExperimentRunner:
    """质量实验运行器"""
    
    def __init__(self):
        self.client = LLMClient()
        self.results = {}
        
    def load_test_data(self, file_path: str, max_questions: int = None) -> List[Dict[str, Any]]:
        """加载测试数据"""
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if line.strip():
                        data.append(json.loads(line.strip()))
                    if max_questions and len(data) >= max_questions:
                        break
            print(f"✅ 成功加载 {len(data)} 条测试数据")
            return data
        except Exception as e:
            print(f"❌ 加载测试数据失败: {e}")
            return []
    
    def run_experiment(self, exp_name: str, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """运行单个实验"""
        exp_config = EXPERIMENTS[exp_name]
        print(f"\n🚀 开始实验: {exp_name} - {exp_config['description']}")
        
        # 创建方法实例
        method = QualityExperimentMethod({
            'corruption_type': exp_config['corruption_type'],
            'n_examples': 8,
            'method_name': exp_name
        })
        
        # 准备问题列表
        questions = []
        for item in test_data:
            # 从answer字段提取ground truth
            answer_text = item.get('answer', '')
            ground_truth = extract_ans_from_response(answer_text)
            questions.append((item['question'], ground_truth))
        
        # 顺序处理（避免并发问题）
        results = []
        total = len(questions)
        for idx, (question, ground_truth) in enumerate(questions, 1):
            try:
                result = method.solve(question, ground_truth)
                results.append({
                    'question': result.question,
                    'ground_truth': result.ground_truth,
                    'predicted_answer': result.predicted_answer,
                    'response': result.response,
                    'token_stats': result.token_stats,
                    'correct': result.correct,
                    'processing_time': result.processing_time,
                    'error': result.error
                })
                if (idx % 10 == 0) or (idx == total):
                    print(f"  进度: {idx}/{total} ({idx/total*100:.1f}%)")
            except Exception as e:
                print(f"  ⚠️ 问题 {idx} 处理失败: {e}")
                results.append({
                    'question': question,
                    'ground_truth': ground_truth,
                    'predicted_answer': None,
                    'response': None,
                    'token_stats': {},
                    'correct': False,
                    'processing_time': 0.0,
                    'error': str(e)
                })
        
        print(f"✅ 实验 {exp_name} 完成，处理了 {len(results)} 个问题")
        return results
    
    def calculate_accuracy(self, results: List[Dict[str, Any]]) -> float:
        """计算准确率"""
        correct_count = sum(1 for r in results if r.get('correct', False))
        total_count = len(results)
        return correct_count / total_count if total_count > 0 else 0.0
    
    def save_results(self, results: List[Dict[str, Any]], filename: str):
        """保存结果"""
        os.makedirs('output/results', exist_ok=True)
        filepath = os.path.join('output/results', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        print(f"✅ 结果已保存到: {filepath}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='提示质量实验')
    parser.add_argument('--test-file', default=config.TEST_FILE, help='测试文件路径')
    parser.add_argument('--max-questions', type=int, default=None, help='最大处理问题数量（默认：全部）')
    parser.add_argument('--experiment', choices=list(EXPERIMENTS.keys()) + ['all'], 
                       default='all', help='要运行的实验')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    print("🎯 提示质量实验开始")
    print("=" * 60)
    
    # 验证配置
    if not config.validate():
        print("❌ 配置验证失败")
        return
    
    # 测试API连接
    runner = QualityExperimentRunner()
    if not runner.client.test_connection():
        print("❌ API连接测试失败")
        return
    
    # 加载测试数据
    test_data = runner.load_test_data(args.test_file, args.max_questions)
    if not test_data:
        print("❌ 无法加载测试数据")
        return
    
    # 确定要运行的实验
    experiments_to_run = list(EXPERIMENTS.keys()) if args.experiment == 'all' else [args.experiment]
    
    # 运行实验
    all_results = {}
    total_start_time = time.time()
    
    for exp_name in experiments_to_run:
        exp_start_time = time.time()
        results = runner.run_experiment(exp_name, test_data)
        exp_time = time.time() - exp_start_time
        
        accuracy = runner.calculate_accuracy(results)
        all_results[exp_name] = {
            'accuracy': accuracy,
            'results': results,
            'time': exp_time
        }
        
        # 保存结果
        runner.save_results(results, f'quality_{exp_name}.jsonl')
        
        print(f"📊 {exp_name} 准确率: {accuracy:.4f} ({accuracy*100:.2f}%) | 耗时: {exp_time:.1f}秒")
    
    total_time = time.time() - total_start_time
    
    # 生成对比报告
    print("\n" + "=" * 60)
    print("📈 实验对比结果")
    print("=" * 60)
    print(f"{'实验名称':<25} {'准确率':<15} {'描述':<30}")
    print("-" * 60)
    
    baseline_acc = all_results.get('baseline', {}).get('accuracy', 0)
    for exp_name in experiments_to_run:
        if exp_name in all_results:
            exp_config = EXPERIMENTS[exp_name]
            accuracy = all_results[exp_name]['accuracy']
            change = (accuracy - baseline_acc) / baseline_acc * 100 if baseline_acc > 0 else 0
            change_str = f"{change:+.2f}%" if baseline_acc > 0 else "N/A"
            print(f"{exp_name:<25} {accuracy*100:>6.2f}% ({change_str:<8}) {exp_config['description']:<30}")
    
    print(f"\n总耗时: {total_time:.1f}秒")
    print("\n🎉 所有实验完成！")


if __name__ == "__main__":
    main()

