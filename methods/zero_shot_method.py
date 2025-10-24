"""
Zero-shot方法实现
"""
from typing import List, Dict, Any, Tuple
import time
from methods.base_method import BaseMethod, MethodResult
from core.llm_client import LLMClient
from core.baseline import nshot_chats
from core.evaluation import extract_ans_from_response

class ZeroShotMethod(BaseMethod):
    """Zero-shot prompting方法"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = LLMClient()
    
    def solve(self, question: str, ground_truth: Any = None) -> MethodResult:
        """解决单个问题"""
        start_time = time.time()
        
        try:
            # 构建zero-shot prompt
            messages = nshot_chats(n=0, question=question)
            
            # 调用LLM
            response, token_stats = self.client.generate_response(messages)
            
            # 提取答案
            predicted_answer = extract_ans_from_response(response)
            
            processing_time = time.time() - start_time
            correct = (predicted_answer == ground_truth) if ground_truth is not None else False
            
            return MethodResult(
                method_name=self.method_name,
                question=question,
                ground_truth=ground_truth,
                predicted_answer=predicted_answer,
                response=response,
                token_stats=token_stats,
                processing_time=processing_time,
                correct=correct
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return MethodResult(
                method_name=self.method_name,
                question=question,
                ground_truth=ground_truth,
                predicted_answer=None,
                response=None,
                token_stats={},
                processing_time=processing_time,
                correct=False,
                error=str(e)
            )
    
    def batch_solve(self, questions: List[Tuple[str, Any]]) -> List[MethodResult]:
        """批量解决问题"""
        results = []
        for question, ground_truth in questions:
            result = self.solve(question, ground_truth)
            results.append(result)
        return results
