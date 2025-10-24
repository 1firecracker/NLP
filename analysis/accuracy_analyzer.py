"""
准确率分析器
"""
from typing import List, Dict, Any
import numpy as np
from analysis.base_analyzer import BaseAnalyzer
from methods.base_method import MethodResult

class AccuracyAnalyzer(BaseAnalyzer):
    """准确率分析器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
    
    def analyze(self, results: List[MethodResult]) -> Dict[str, Any]:
        """分析准确率相关指标"""
        if not results:
            return {"error": "No results to analyze"}
        
        df = self.to_dataframe(results)
        
        # 基础统计
        total_questions = len(results)
        correct_answers = df['correct'].sum()
        accuracy = correct_answers / total_questions if total_questions > 0 else 0
        
        # 按方法分组统计
        method_stats = {}
        for method in df['method_name'].unique():
            method_df = df[df['method_name'] == method]
            method_correct = method_df['correct'].sum()
            method_total = len(method_df)
            method_accuracy = method_correct / method_total if method_total > 0 else 0
            
            method_stats[method] = {
                "total_questions": method_total,
                "correct_answers": method_correct,
                "accuracy": method_accuracy,
                "error_rate": 1 - method_accuracy
            }
        
        # 错误分析
        error_analysis = self._analyze_errors(df)
        
        return {
            "overall": {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "accuracy": accuracy,
                "error_rate": 1 - accuracy
            },
            "by_method": method_stats,
            "error_analysis": error_analysis,
            "analyzer": self.get_analyzer_info()
        }
    
    def _analyze_errors(self, df) -> Dict[str, Any]:
        """分析错误类型"""
        error_df = df[df['correct'] == False]
        
        if len(error_df) == 0:
            return {"no_errors": True}
        
        # 错误统计
        error_count = len(error_df)
        error_rate = error_count / len(df)
        
        # 按方法统计错误
        method_errors = {}
        for method in error_df['method_name'].unique():
            method_error_df = error_df[error_df['method_name'] == method]
            method_errors[method] = {
                "error_count": len(method_error_df),
                "error_rate": len(method_error_df) / len(df[df['method_name'] == method])
            }
        
        return {
            "total_errors": error_count,
            "error_rate": error_rate,
            "by_method": method_errors
        }
    
    def get_metrics(self) -> List[str]:
        """获取支持的指标列表"""
        return [
            "accuracy",
            "error_rate", 
            "correct_answers",
            "total_questions",
            "method_comparison"
        ]
