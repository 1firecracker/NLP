"""
成本分析器
符合作业要求的Token成本分析
"""
from typing import List, Dict, Any
import numpy as np
from analysis.base_analyzer import BaseAnalyzer
from methods.base_method import MethodResult

class CostAnalyzer(BaseAnalyzer):
    """成本分析器 - 符合作业要求"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # 假设的Token成本 (可根据实际API调整)
        self.input_token_cost = config.get('input_token_cost', 0.0001)  # 每1000个输入token的成本
        self.output_token_cost = config.get('output_token_cost', 0.0002)  # 每1000个输出token的成本
    
    def analyze(self, results: List[MethodResult]) -> Dict[str, Any]:
        """分析成本相关指标"""
        if not results:
            return {"error": "No results to analyze"}
        
        df = self.to_dataframe(results)
        
        # 总体成本统计
        total_input_tokens = df['prompt_tokens'].sum()
        total_output_tokens = df['completion_tokens'].sum()
        total_tokens = df['total_tokens'].sum()
        
        # 成本计算
        input_cost = (total_input_tokens / 1000) * self.input_token_cost
        output_cost = (total_output_tokens / 1000) * self.output_token_cost
        total_cost = input_cost + output_cost
        
        # 平均成本
        avg_tokens_per_question = total_tokens / len(results) if len(results) > 0 else 0
        avg_cost_per_question = total_cost / len(results) if len(results) > 0 else 0
        
        # 按方法分组统计
        method_costs = {}
        for method in df['method_name'].unique():
            method_df = df[df['method_name'] == method]
            method_input_tokens = method_df['prompt_tokens'].sum()
            method_output_tokens = method_df['completion_tokens'].sum()
            method_total_tokens = method_df['total_tokens'].sum()
            
            method_input_cost = (method_input_tokens / 1000) * self.input_token_cost
            method_output_cost = (method_output_tokens / 1000) * self.output_token_cost
            method_total_cost = method_input_cost + method_output_cost
            
            method_costs[method] = {
                "input_tokens": method_input_tokens,
                "output_tokens": method_output_tokens,
                "total_tokens": method_total_tokens,
                "input_cost": method_input_cost,
                "output_cost": method_output_cost,
                "total_cost": method_total_cost,
                "avg_tokens_per_question": method_total_tokens / len(method_df),
                "avg_cost_per_question": method_total_cost / len(method_df)
            }
        
        # 效率分析
        efficiency_analysis = self._analyze_efficiency(df)
        
        return {
            "overall": {
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tokens": total_tokens,
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total_cost": total_cost,
                "avg_tokens_per_question": avg_tokens_per_question,
                "avg_cost_per_question": avg_cost_per_question
            },
            "by_method": method_costs,
            "efficiency_analysis": efficiency_analysis,
            "cost_breakdown": {
                "input_token_cost_per_1k": self.input_token_cost,
                "output_token_cost_per_1k": self.output_token_cost
            },
            "analyzer": self.get_analyzer_info()
        }
    
    def _analyze_efficiency(self, df) -> Dict[str, Any]:
        """分析效率指标"""
        # 计算每个问题的Token效率
        df['tokens_per_correct'] = df['total_tokens'] / df['correct'].astype(int)
        df['cost_per_correct'] = (df['total_tokens'] / 1000) * (self.input_token_cost + self.output_token_cost) / df['correct'].astype(int)
        
        # 按方法统计效率
        efficiency_by_method = {}
        for method in df['method_name'].unique():
            method_df = df[df['method_name'] == method]
            correct_df = method_df[method_df['correct'] == True]
            
            if len(correct_df) > 0:
                avg_tokens_per_correct = correct_df['total_tokens'].mean()
                avg_cost_per_correct = (correct_df['total_tokens'] / 1000 * (self.input_token_cost + self.output_token_cost)).mean()
            else:
                avg_tokens_per_correct = float('inf')
                avg_cost_per_correct = float('inf')
            
            efficiency_by_method[method] = {
                "avg_tokens_per_correct": avg_tokens_per_correct,
                "avg_cost_per_correct": avg_cost_per_correct,
                "efficiency_score": 1 / avg_tokens_per_correct if avg_tokens_per_correct != float('inf') else 0
            }
        
        return efficiency_by_method
    
    def get_metrics(self) -> List[str]:
        """获取支持的指标列表"""
        return [
            "total_tokens",
            "input_tokens", 
            "output_tokens",
            "total_cost",
            "avg_cost_per_question",
            "efficiency_score"
        ]
