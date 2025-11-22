"""
提示质量实验结果分析模块
"""
import json
import os
from typing import List, Dict, Any
from collections import defaultdict
from pathlib import Path


class QualityAnalyzer:
    """质量分析器"""
    
    def __init__(self, results_dir: str = 'output/results'):
        self.results_dir = results_dir
    
    def load_results(self, filename: str) -> List[Dict[str, Any]]:
        """加载结果文件"""
        filepath = os.path.join(self.results_dir, filename)
        if not os.path.exists(filepath):
            return []
        results = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line.strip()))
        return results
    
    def calculate_accuracy(self, results: List[Dict[str, Any]]) -> float:
        """计算准确率"""
        if not results:
            return 0.0
        correct_count = sum(1 for r in results if r.get('correct', False))
        return correct_count / len(results)
    
    def analyze_accuracy_by_dimension(self) -> Dict[str, Dict[str, float]]:
        """按维度分析准确率"""
        dimensions = {
            'correctness': ['baseline', 'wrong_answer', 'wrong_reasoning', 'completely_wrong'],
            'relevance': ['baseline', 'irrelevant', 'partially_relevant', 'mixed_50_50'],
            'format': ['baseline', 'format_inconsistent', 'format_missing', 'format_chaotic']
        }
        
        analysis = {}
        for dim_name, exp_names in dimensions.items():
            dim_results = {}
            for exp_name in exp_names:
                filename = f'quality_{exp_name}.jsonl'
                results = self.load_results(filename)
                if results:
                    accuracy = self.calculate_accuracy(results)
                    dim_results[exp_name] = accuracy
            if dim_results:
                analysis[dim_name] = dim_results
        
        return analysis
    
    def analyze_error_types(self, exp_name: str) -> Dict[str, int]:
        """分析错误类型"""
        filename = f'quality_{exp_name}.jsonl'
        results = self.load_results(filename)
        
        if not results:
            return {}
        
        error_types = {
            'extraction_failed': 0,  # 无法提取答案
            'completely_wrong': 0,   # 完全错误
            'close_but_wrong': 0,    # 接近但错误（±5以内）
            'format_error': 0,        # 格式错误
            'correct': 0              # 正确
        }
        
        for result in results:
            if result.get('correct', False):
                error_types['correct'] += 1
            else:
                pred = result.get('predicted_answer')
                truth = result.get('ground_truth')
                
                if pred is None or pred == '':
                    error_types['extraction_failed'] += 1
                elif truth is not None and isinstance(truth, (int, float)):
                    try:
                        pred_num = float(pred) if isinstance(pred, str) else pred
                        if isinstance(pred_num, (int, float)):
                            diff = abs(truth - pred_num)
                            if diff <= 5:
                                error_types['close_but_wrong'] += 1
                            else:
                                error_types['completely_wrong'] += 1
                        else:
                            error_types['format_error'] += 1
                    except (ValueError, TypeError):
                        error_types['format_error'] += 1
                else:
                    error_types['format_error'] += 1
        
        return error_types
    
    def analyze_token_usage(self, exp_name: str) -> Dict[str, Any]:
        """分析Token使用情况"""
        filename = f'quality_{exp_name}.jsonl'
        results = self.load_results(filename)
        
        if not results:
            return {}
        
        total_input = 0
        total_output = 0
        total_time = 0.0
        
        for result in results:
            token_stats = result.get('token_stats', {})
            total_input += token_stats.get('prompt_tokens', 0)
            total_output += token_stats.get('completion_tokens', 0)
            total_time += result.get('processing_time', 0.0)
        
        n = len(results)
        return {
            'total_input_tokens': total_input,
            'total_output_tokens': total_output,
            'total_tokens': total_input + total_output,
            'avg_input_tokens': total_input / n if n > 0 else 0,
            'avg_output_tokens': total_output / n if n > 0 else 0,
            'avg_tokens_per_question': (total_input + total_output) / n if n > 0 else 0,
            'avg_time_per_question': total_time / n if n > 0 else 0,
            'total_questions': n
        }
    
    def generate_comparison_report(self) -> str:
        """生成对比报告"""
        analysis = self.analyze_accuracy_by_dimension()
        
        if not analysis:
            return "# 提示质量实验对比报告\n\n暂无数据，请先运行实验。\n"
        
        report = "# 提示质量实验对比报告\n\n"
        
        # 获取基线准确率
        baseline_acc = 0
        if 'correctness' in analysis and 'baseline' in analysis['correctness']:
            baseline_acc = analysis['correctness']['baseline']
        elif 'relevance' in analysis and 'baseline' in analysis['relevance']:
            baseline_acc = analysis['relevance']['baseline']
        elif 'format' in analysis and 'baseline' in analysis['format']:
            baseline_acc = analysis['format']['baseline']
        
        for dim_name, dim_results in analysis.items():
            report += f"## {dim_name.upper()} 维度\n\n"
            report += f"| 实验组 | 准确率 | 相对基线变化 |\n"
            report += f"|--------|--------|--------------|\n"
            
            dim_baseline = dim_results.get('baseline', baseline_acc)
            for exp_name, accuracy in sorted(dim_results.items()):
                if dim_baseline > 0:
                    change = (accuracy - dim_baseline) / dim_baseline * 100
                    change_str = f"{change:+.2f}%"
                else:
                    change_str = "N/A"
                report += f"| {exp_name} | {accuracy*100:.2f}% | {change_str} |\n"
            
            report += "\n"
        
        # 添加错误类型分析
        report += "## 错误类型分析\n\n"
        report += "| 实验组 | 正确 | 提取失败 | 完全错误 | 接近错误 | 格式错误 |\n"
        report += "|--------|------|----------|----------|----------|----------|\n"
        
        all_exp_names = set()
        for dim_results in analysis.values():
            all_exp_names.update(dim_results.keys())
        
        for exp_name in sorted(all_exp_names):
            error_types = self.analyze_error_types(exp_name)
            if error_types:
                total = sum(error_types.values())
                if total > 0:
                    report += f"| {exp_name} | {error_types.get('correct', 0)} ({error_types.get('correct', 0)/total*100:.1f}%) | "
                    report += f"{error_types.get('extraction_failed', 0)} ({error_types.get('extraction_failed', 0)/total*100:.1f}%) | "
                    report += f"{error_types.get('completely_wrong', 0)} ({error_types.get('completely_wrong', 0)/total*100:.1f}%) | "
                    report += f"{error_types.get('close_but_wrong', 0)} ({error_types.get('close_but_wrong', 0)/total*100:.1f}%) | "
                    report += f"{error_types.get('format_error', 0)} ({error_types.get('format_error', 0)/total*100:.1f}%) |\n"
        
        report += "\n"
        
        # 添加Token使用分析
        report += "## Token使用分析\n\n"
        report += "| 实验组 | 平均输入Token | 平均输出Token | 平均总Token | 平均时间(秒) |\n"
        report += "|--------|--------------|--------------|------------|-------------|\n"
        
        for exp_name in sorted(all_exp_names):
            token_usage = self.analyze_token_usage(exp_name)
            if token_usage:
                report += f"| {exp_name} | {token_usage.get('avg_input_tokens', 0):.1f} | "
                report += f"{token_usage.get('avg_output_tokens', 0):.1f} | "
                report += f"{token_usage.get('avg_tokens_per_question', 0):.1f} | "
                report += f"{token_usage.get('avg_time_per_question', 0):.2f} |\n"
        
        return report
    
    def save_report(self, output_file: str = 'output/quality_experiment_report.md'):
        """保存报告到文件"""
        report = self.generate_comparison_report()
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存到: {output_file}")


if __name__ == "__main__":
    analyzer = QualityAnalyzer()
    report = analyzer.generate_comparison_report()
    print(report)
    analyzer.save_report()

