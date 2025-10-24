"""
方法比较器
比较不同prompting方法的效果和性能
"""
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class MethodResult:
    """方法结果数据类"""
    method_name: str
    accuracy: float
    total_questions: int
    correct_answers: int
    avg_processing_time: float
    total_processing_time: float
    avg_token_usage: int
    total_token_usage: int
    avg_confidence: float
    error_rate: float
    results: List[Dict[str, Any]]

class MethodComparator:
    """方法比较器"""
    
    def __init__(self):
        """初始化比较器"""
        self.results = {}
        self.comparison_metrics = [
            "accuracy",
            "avg_processing_time", 
            "avg_token_usage",
            "avg_confidence",
            "error_rate"
        ]
    
    def add_method_result(self, result: MethodResult):
        """
        添加方法结果
        
        Args:
            result: 方法结果
        """
        self.results[result.method_name] = result
        print(f"✅ 已添加方法结果: {result.method_name}")
        print(f"  准确率: {result.accuracy:.4f}")
        print(f"  平均处理时间: {result.avg_processing_time:.2f}秒")
        print(f"  平均Token使用: {result.avg_token_usage}")
    
    def compare_all_methods(self) -> Dict[str, Any]:
        """
        比较所有方法
        
        Returns:
            Dict[str, Any]: 比较结果
        """
        if len(self.results) < 2:
            return {"error": "需要至少两种方法的结果进行比较"}
        
        comparison = {
            "methods": list(self.results.keys()),
            "metrics": {},
            "rankings": {},
            "best_method": None,
            "detailed_comparison": {}
        }
        
        # 计算各项指标的排名
        for metric in self.comparison_metrics:
            values = {}
            for method_name, result in self.results.items():
                if metric == "accuracy":
                    values[method_name] = result.accuracy
                elif metric == "avg_processing_time":
                    values[method_name] = result.avg_processing_time
                elif metric == "avg_token_usage":
                    values[method_name] = result.avg_token_usage
                elif metric == "avg_confidence":
                    values[method_name] = result.avg_confidence
                elif metric == "error_rate":
                    values[method_name] = result.error_rate
            
            comparison["metrics"][metric] = values
            
            # 计算排名 (准确率和置信度越高越好，其他越低越好)
            if metric in ["accuracy", "avg_confidence"]:
                ranking = sorted(values.items(), key=lambda x: x[1], reverse=True)
            else:
                ranking = sorted(values.items(), key=lambda x: x[1])
            
            comparison["rankings"][metric] = ranking
        
        # 计算综合评分
        composite_scores = self._calculate_composite_scores()
        comparison["composite_scores"] = composite_scores
        
        # 找出最佳方法
        best_method = max(composite_scores.items(), key=lambda x: x[1])[0]
        comparison["best_method"] = best_method
        
        # 详细比较
        comparison["detailed_comparison"] = self._create_detailed_comparison()
        
        return comparison
    
    def _calculate_composite_scores(self) -> Dict[str, float]:
        """计算综合评分"""
        scores = {}
        
        for method_name, result in self.results.items():
            # 标准化各项指标 (0-1之间)
            accuracy_score = result.accuracy
            
            # 处理时间评分 (时间越短越好)
            max_time = max(r.avg_processing_time for r in self.results.values())
            time_score = 1 - (result.avg_processing_time / max_time) if max_time > 0 else 1
            
            # Token使用量评分 (使用量越少越好)
            max_tokens = max(r.avg_token_usage for r in self.results.values())
            token_score = 1 - (result.avg_token_usage / max_tokens) if max_tokens > 0 else 1
            
            # 置信度评分
            confidence_score = result.avg_confidence
            
            # 错误率评分 (错误率越低越好)
            error_score = 1 - result.error_rate
            
            # 综合评分 (权重: 准确率40%, 时间20%, Token20%, 置信度10%, 错误率10%)
            composite_score = (
                accuracy_score * 0.4 +
                time_score * 0.2 +
                token_score * 0.2 +
                confidence_score * 0.1 +
                error_score * 0.1
            )
            
            scores[method_name] = composite_score
        
        return scores
    
    def _create_detailed_comparison(self) -> Dict[str, Any]:
        """创建详细比较"""
        detailed = {}
        
        for method_name, result in self.results.items():
            detailed[method_name] = {
                "accuracy": result.accuracy,
                "total_questions": result.total_questions,
                "correct_answers": result.correct_answers,
                "avg_processing_time": result.avg_processing_time,
                "total_processing_time": result.total_processing_time,
                "avg_token_usage": result.avg_token_usage,
                "total_token_usage": result.total_token_usage,
                "avg_confidence": result.avg_confidence,
                "error_rate": result.error_rate
            }
        
        return detailed
    
    def create_comparison_chart(self, save_path: str = None):
        """
        创建比较图表
        
        Args:
            save_path: 保存路径
            
        Returns:
            plt.Figure: 图表对象
        """
        if len(self.results) < 2:
            print("❌ 需要至少两种方法的结果进行比较")
            return None
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            print("❌ 需要安装matplotlib和numpy进行可视化")
            return None
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('方法比较分析', fontsize=16, fontweight='bold')
        
        methods = list(self.results.keys())
        colors = plt.cm.Set3(np.linspace(0, 1, len(methods)))
        
        # 准确率比较
        accuracies = [self.results[method].accuracy for method in methods]
        bars1 = axes[0, 0].bar(methods, accuracies, color=colors)
        axes[0, 0].set_title('准确率比较', fontweight='bold')
        axes[0, 0].set_ylabel('准确率')
        axes[0, 0].set_ylim(0, 1)
        
        # 添加数值标签
        for bar, acc in zip(bars1, accuracies):
            axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                           f'{acc:.3f}', ha='center', va='bottom')
        
        # 处理时间比较
        times = [self.results[method].avg_processing_time for method in methods]
        bars2 = axes[0, 1].bar(methods, times, color=colors)
        axes[0, 1].set_title('平均处理时间比较', fontweight='bold')
        axes[0, 1].set_ylabel('时间 (秒)')
        
        for bar, time in zip(bars2, times):
            axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                           f'{time:.2f}s', ha='center', va='bottom')
        
        # Token使用量比较
        tokens = [self.results[method].avg_token_usage for method in methods]
        bars3 = axes[0, 2].bar(methods, tokens, color=colors)
        axes[0, 2].set_title('平均Token使用量比较', fontweight='bold')
        axes[0, 2].set_ylabel('Token数量')
        
        for bar, token in zip(bars3, tokens):
            axes[0, 2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                           f'{token}', ha='center', va='bottom')
        
        # 置信度比较
        confidences = [self.results[method].avg_confidence for method in methods]
        bars4 = axes[1, 0].bar(methods, confidences, color=colors)
        axes[1, 0].set_title('平均置信度比较', fontweight='bold')
        axes[1, 0].set_ylabel('置信度')
        axes[1, 0].set_ylim(0, 1)
        
        for bar, conf in zip(bars4, confidences):
            axes[1, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                           f'{conf:.3f}', ha='center', va='bottom')
        
        # 错误率比较
        errors = [self.results[method].error_rate for method in methods]
        bars5 = axes[1, 1].bar(methods, errors, color=colors)
        axes[1, 1].set_title('错误率比较', fontweight='bold')
        axes[1, 1].set_ylabel('错误率')
        axes[1, 1].set_ylim(0, 1)
        
        for bar, err in zip(bars5, errors):
            axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                           f'{err:.3f}', ha='center', va='bottom')
        
        # 综合评分比较
        composite_scores = self._calculate_composite_scores()
        scores = [composite_scores[method] for method in methods]
        bars6 = axes[1, 2].bar(methods, scores, color=colors)
        axes[1, 2].set_title('综合评分比较', fontweight='bold')
        axes[1, 2].set_ylabel('综合评分')
        
        for bar, score in zip(bars6, scores):
            axes[1, 2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                           f'{score:.3f}', ha='center', va='bottom')
        
        # 旋转x轴标签
        for ax in axes.flat:
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 比较图表已保存到: {save_path}")
        
        return fig
    
    def generate_report(self, output_path: str = None) -> str:
        """
        生成比较报告
        
        Args:
            output_path: 输出路径
            
        Returns:
            str: 报告内容
        """
        comparison = self.compare_all_methods()
        
        report_lines = []
        report_lines.append("# 方法比较报告")
        report_lines.append("=" * 50)
        report_lines.append("")
        
        # 基本信息
        report_lines.append("## 基本信息")
        report_lines.append(f"- 比较方法数量: {len(self.results)}")
        report_lines.append(f"- 方法列表: {', '.join(comparison['methods'])}")
        report_lines.append(f"- 最佳方法: {comparison['best_method']}")
        report_lines.append("")
        
        # 详细比较
        report_lines.append("## 详细比较")
        for method_name, result in self.results.items():
            report_lines.append(f"### {method_name}")
            report_lines.append(f"- 准确率: {result.accuracy:.4f}")
            report_lines.append(f"- 总问题数: {result.total_questions}")
            report_lines.append(f"- 正确答案数: {result.correct_answers}")
            report_lines.append(f"- 平均处理时间: {result.avg_processing_time:.2f}秒")
            report_lines.append(f"- 总处理时间: {result.total_processing_time:.2f}秒")
            report_lines.append(f"- 平均Token使用: {result.avg_token_usage}")
            report_lines.append(f"- 总Token使用: {result.total_token_usage}")
            report_lines.append(f"- 平均置信度: {result.avg_confidence:.4f}")
            report_lines.append(f"- 错误率: {result.error_rate:.4f}")
            report_lines.append("")
        
        # 排名
        report_lines.append("## 各项指标排名")
        for metric, ranking in comparison["rankings"].items():
            report_lines.append(f"### {metric}")
            for i, (method, value) in enumerate(ranking, 1):
                report_lines.append(f"{i}. {method}: {value:.4f}")
            report_lines.append("")
        
        # 综合评分
        report_lines.append("## 综合评分")
        composite_scores = comparison["composite_scores"]
        sorted_scores = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)
        for i, (method, score) in enumerate(sorted_scores, 1):
            report_lines.append(f"{i}. {method}: {score:.4f}")
        
        report_content = "\n".join(report_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ 比较报告已保存到: {output_path}")
        
        return report_content
    
    def export_results(self, output_path: str):
        """导出结果到JSON文件"""
        comparison = self.compare_all_methods()
        
        export_data = {
            "comparison": comparison,
            "raw_results": {name: {
                "accuracy": result.accuracy,
                "total_questions": result.total_questions,
                "correct_answers": result.correct_answers,
                "avg_processing_time": result.avg_processing_time,
                "total_processing_time": result.total_processing_time,
                "avg_token_usage": result.avg_token_usage,
                "total_token_usage": result.total_token_usage,
                "avg_confidence": result.avg_confidence,
                "error_rate": result.error_rate
            } for name, result in self.results.items()}
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 比较结果已导出到: {output_path}")
