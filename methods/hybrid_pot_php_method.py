"""
混合PoT和PHP策略方法
结合Program of Thoughts和Progressive-Hint的优势
"""
import time
from typing import List, Dict, Any
from methods.base_method import BaseMethod, MethodResult
from methods.program_of_thoughts_method import ProgramOfThoughtsMethod
from methods.progressive_hint_method import ProgressiveHintMethod
from data.config import config

class HybridPoTPHPMethod(BaseMethod):
    """混合PoT和PHP策略方法"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.method_name = "HybridPoTPHP"
    
    def solve(self, question: str, ground_truth: Any = None) -> MethodResult:
        """混合策略解决单个问题"""
        start_time = time.time()
        
        # 1. 首先尝试PoT方法（温度0.1，Zero-shot）
        pot_result = self._try_pot_with_config(
            question, ground_truth,
            temperature=0.2,
            use_few_shot=False
        )
        
        # 2. 如果PoT成功且正确，直接返回
        if pot_result.correct:
            processing_time = time.time() - start_time
            return MethodResult(
                method_name=self.method_name,
                question=question,
                ground_truth=ground_truth,
                predicted_answer=pot_result.predicted_answer,
                response=pot_result.response,
                token_stats=pot_result.token_stats,
                processing_time=processing_time,
                correct=pot_result.correct,
                metadata={"strategy_used": "pot", "fallback_used": False}
            )
        
        # 3. PoT失败，尝试PHP方法（温度0.5，Few-shot）
        php_result = self._try_php_with_config(
            question, ground_truth,
            temperature=0.5,
            use_few_shot=True
        )
        
        processing_time = time.time() - start_time
        
        # 4. 返回PHP结果
        return MethodResult(
            method_name=self.method_name,
            question=question,
            ground_truth=ground_truth,
            predicted_answer=php_result.predicted_answer,
            response=php_result.response,
            token_stats=php_result.token_stats,
            processing_time=processing_time,
            correct=php_result.correct,
            metadata={"strategy_used": "php", "fallback_used": True}
        )
    
    def _try_pot_with_config(self, question: str, ground_truth: Any,
                           temperature: float, use_few_shot: bool) -> MethodResult:
        """使用特定配置尝试PoT方法"""
        # 保存原始配置
        original_temp = config.TEMPERATURE
        
        try:
            # 临时覆盖配置
            config.TEMPERATURE = temperature
            
            # 创建PoT方法实例
            pot_method = ProgramOfThoughtsMethod({})
            return pot_method.solve(question, ground_truth)
        finally:
            # 恢复原始配置
            config.TEMPERATURE = original_temp
    
    def _try_php_with_config(self, question: str, ground_truth: Any,
                            temperature: float, use_few_shot: bool) -> MethodResult:
        """使用特定配置尝试PHP方法"""
        # 保存原始配置
        original_temp = config.TEMPERATURE
        
        try:
            # 临时覆盖配置
            config.TEMPERATURE = temperature
            
            # 创建PHP方法实例
            php_method = ProgressiveHintMethod({})
            return php_method.solve(question, ground_truth)
        finally:
            # 恢复原始配置
            config.TEMPERATURE = original_temp
    
    def batch_solve(self, questions: List[tuple]) -> List[MethodResult]:
        """批量解决问题"""
        results = []
        for question, ground_truth in questions:
            result = self.solve(question, ground_truth)
            results.append(result)
        return results
