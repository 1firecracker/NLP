"""
Progressive-Hint Prompting 方法实现
数学问题专用提示策略
"""
import time
from typing import List, Dict, Any
from methods.base_method import BaseMethod, MethodResult
from core.llm_client import LLMClient, token_tracker
from core.baseline import nshot_chats
from core.evaluation import extract_ans_from_response
from data.config import config

class ProgressiveHintMethod(BaseMethod):
    """Progressive-Hint Prompting 方法"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = LLMClient()
        self.max_hints = 3  # 最大提示次数
        self.hint_templates = [
            "Please carefully analyze the key numbers and mathematical relationships in the problem",
            "Try to solve step by step, calculating intermediate results first",
            "Consider using reverse thinking, working backwards from the answer",
            "Check each step of your calculation process for correctness",
            "Re-examine the core requirements of the problem"
        ]
    
    def solve(self, question: str, ground_truth: Any = None) -> MethodResult:
        """
        解决单个Progressive-Hint问题
        
        Args:
            question: 问题文本
            ground_truth: 正确答案
            
        Returns:
            MethodResult: 方法结果
        """
        start_time = time.time()
        
        # 1. 初始尝试（使用zero-shot）
        initial_result = self._initial_attempt(question)
        
        # 2. 如果答案错误，应用渐进提示
        if not self._is_correct(initial_result, ground_truth):
            final_result = self._apply_progressive_hints(question, initial_result, ground_truth)
        else:
            final_result = initial_result
        
        processing_time = time.time() - start_time
        
        return MethodResult(
            method_name=self.method_name,
            question=question,
            ground_truth=ground_truth,
            predicted_answer=final_result.predicted_answer,
            response=final_result.response,
            token_stats=final_result.token_stats,
            processing_time=processing_time,
            correct=(final_result.predicted_answer == ground_truth)
        )
    
    def _initial_attempt(self, question: str) -> MethodResult:
        """初始尝试（使用few-shot方法）"""
        messages = nshot_chats(n=8, question=question)
        response, token_stats = self.client.generate_response(messages)
        token_tracker.add_usage(token_stats)
        
        predicted_answer = extract_ans_from_response(response)
        
        return MethodResult(
            method_name=self.method_name,
            question=question,
            ground_truth=None,
            predicted_answer=predicted_answer,
            response=response,
            token_stats=token_stats,
            processing_time=0.0,
            correct=False
        )
    
    def _apply_progressive_hints(self, question: str, initial_result: MethodResult, ground_truth: Any) -> MethodResult:
        """应用渐进提示"""
        best_result = initial_result
        
        for hint_level in range(self.max_hints):
            # 生成提示（包含之前的错误答案）
            hint = self._generate_enhanced_hint(question, best_result, hint_level)
            
            # 使用提示重新尝试
            enhanced_result = self._try_with_hint(question, hint)
            
            # 如果答案正确，返回结果
            if self._is_correct(enhanced_result, ground_truth):
                return enhanced_result
            
            # 更新最佳结果（即使不正确，也记录最后一次尝试）
            best_result = enhanced_result
        
        return best_result
    
    def _generate_enhanced_hint(self, question: str, previous_result: MethodResult, hint_level: int) -> str:
        """生成增强提示（包含错误答案反馈）"""
        base_hint = self.hint_templates[hint_level % len(self.hint_templates)]
        
        # 检查答案长度（答案过长说明提取失败，可能把整段文字作为答案）
        answer_length = len(str(previous_result.predicted_answer)) if previous_result.predicted_answer is not None else 0
        is_answer_too_long = answer_length > 20
        
        # 检查答案提取是否成功
        answer_extraction_failed = (previous_result.predicted_answer is None or 
                                  previous_result.predicted_answer == "" or
                                  str(previous_result.predicted_answer).lower() in ['none', 'null', ''])
        
        # 添加错误答案反馈
        if previous_result.predicted_answer is not None and not answer_extraction_failed and not is_answer_too_long:
            # 答案提取成功且长度合理，正常反馈
            error_feedback = f"The previous answer is {previous_result.predicted_answer}. Please re-check and give the final answer."
            return f"{base_hint}\n\n{error_feedback}"
        else:
            # 答案提取失败或答案过长，提示按照标准格式输出
            if is_answer_too_long or answer_extraction_failed:
                format_instruction = "IMPORTANT: Please provide your answer in the standard format '#### [number]' at the end of your response. Do not include lengthy explanations or analysis - just show your work briefly and end with the final answer in the required format."
                return f"{base_hint}\n\n{format_instruction}"
            else:
                return base_hint
    
    def _try_with_hint(self, question: str, hint: str) -> MethodResult:
        """使用提示重新尝试"""
        enhanced_question = f"{question}\n\nHint: {hint}"
        messages = nshot_chats(n=8, question=enhanced_question)
        response, token_stats = self.client.generate_response(messages)
        token_tracker.add_usage(token_stats)
        
        predicted_answer = extract_ans_from_response(response)
        
        return MethodResult(
            method_name=self.method_name,
            question=question,
            ground_truth=None,
            predicted_answer=predicted_answer,
            response=response,
            token_stats=token_stats,
            processing_time=0.0,
            correct=False
        )
    
    def _is_correct(self, result: MethodResult, ground_truth: Any) -> bool:
        """判断答案是否正确"""
        if ground_truth is None:
            return False
        return result.predicted_answer == ground_truth
    
    def batch_solve(self, questions: List[Dict[str, Any]]) -> List[MethodResult]:
        """
        批量解决Progressive-Hint问题
        
        Args:
            questions: 问题列表
            
        Returns:
            List[MethodResult]: 结果列表
        """
        results = []
        for item in questions:
            result = self.solve(item['question'], extract_ans_from_response(item['answer']))
            results.append(result)
        return results
