"""
基础方法接口
所有prompting方法的基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import time

@dataclass
class MethodResult:
    """统一的方法结果格式"""
    method_name: str
    question: str
    ground_truth: Any
    predicted_answer: Any
    response: str
    token_stats: Dict[str, int]
    processing_time: float
    correct: bool
    error: str = None
    metadata: Dict[str, Any] = None

class BaseMethod(ABC):
    """所有方法的基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.method_name = self.__class__.__name__
    
    @abstractmethod
    def solve(self, question: str, ground_truth: Any = None) -> MethodResult:
        """解决单个问题"""
        pass
    
    @abstractmethod
    def batch_solve(self, questions: List[Tuple[str, Any]]) -> List[MethodResult]:
        """批量解决问题"""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取方法元数据"""
        return {
            "method_name": self.method_name,
            "version": "1.0",
            "description": self.__doc__,
            "config": self.config
        }
    
    def validate_result(self, result: MethodResult) -> bool:
        """验证结果格式"""
        required_fields = ['method_name', 'question', 'predicted_answer', 'correct']
        return all(hasattr(result, field) for field in required_fields)
