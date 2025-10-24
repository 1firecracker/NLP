"""
基础分析器接口
所有分析器的基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd
from methods.base_method import MethodResult

class BaseAnalyzer(ABC):
    """所有分析器的基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.analyzer_name = self.__class__.__name__
    
    @abstractmethod
    def analyze(self, results: List[MethodResult]) -> Dict[str, Any]:
        """分析结果数据"""
        pass
    
    @abstractmethod
    def get_metrics(self) -> List[str]:
        """获取支持的指标列表"""
        pass
    
    def to_dataframe(self, results: List[MethodResult]) -> pd.DataFrame:
        """转换为DataFrame格式"""
        data = []
        for result in results:
            row = {
                'method_name': result.method_name,
                'question': result.question,
                'ground_truth': result.ground_truth,
                'predicted_answer': result.predicted_answer,
                'correct': result.correct,
                'processing_time': result.processing_time,
                'error': result.error,
                'prompt_tokens': result.token_stats.get('prompt_tokens', 0),
                'completion_tokens': result.token_stats.get('completion_tokens', 0),
                'total_tokens': result.token_stats.get('total_tokens', 0)
            }
            data.append(row)
        return pd.DataFrame(data)
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """获取分析器信息"""
        return {
            "analyzer_name": self.analyzer_name,
            "version": "1.0",
            "description": self.__doc__,
            "supported_metrics": self.get_metrics(),
            "config": self.config
        }
