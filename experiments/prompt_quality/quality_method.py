"""
提示质量实验方法类
"""
import time
from typing import List, Dict, Any, Tuple
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from methods.base_method import BaseMethod, MethodResult
from core.llm_client import LLMClient
from core.evaluation import extract_ans_from_response
from core.baseline import gsm8k_nshots
from experiments.prompt_quality.corrupted_demonstrations import (
    CORRUPTION_TYPES,
    get_irrelevant_demonstrations,
    get_partially_relevant_demonstrations,
    get_mixed_demonstrations,
    get_format_inconsistent_demonstrations,
    get_format_missing_demonstrations,
    get_format_chaotic_demonstrations,
)


def nshot_chats_corrupted(n: int, question: str, corruption_type: str = None, 
                          corrupted_demos: List[Tuple[str, str]] = None) -> list:
    """
    使用被干扰的演示构建prompt
    
    Args:
        n: 示例数量
        question: 当前问题
        corruption_type: 干扰类型
        corrupted_demos: 预处理的干扰演示列表
        
    Returns:
        对话消息列表
    """
    def question_prompt(s):
        return f'Question: {s}'

    def answer_prompt(s):
        return f"Answer:\nLet's think step by step.\n{s}"

    chats = [
        {"role": "system", "content": 
         "Your task is to solve a series of math word problems by providing the final answer. Output format: #### integer . e.g.: #### 16 if the answer is 16"}
    ]

    # 选择演示
    if corrupted_demos:
        demos = corrupted_demos[:n]
    elif corruption_type and corruption_type in CORRUPTION_TYPES:
        if corruption_type in ['irrelevant', 'partially_relevant', 'mixed_50_50',
                               'format_inconsistent', 'format_missing', 'format_chaotic']:
            # 这些类型返回完整演示列表
            if corruption_type == 'irrelevant':
                demos = get_irrelevant_demonstrations()[:n]
            elif corruption_type == 'partially_relevant':
                demos = get_partially_relevant_demonstrations()[:n]
            elif corruption_type == 'mixed_50_50':
                demos = get_mixed_demonstrations(0.5)[:n]
            elif corruption_type == 'format_inconsistent':
                demos = get_format_inconsistent_demonstrations()[:n]
            elif corruption_type == 'format_missing':
                demos = get_format_missing_demonstrations()[:n]
            elif corruption_type == 'format_chaotic':
                demos = get_format_chaotic_demonstrations()[:n]
            else:
                demos = gsm8k_nshots[:n]
        else:
            # 这些类型是函数，需要应用到原始演示
            corrupt_func = CORRUPTION_TYPES[corruption_type]
            demos = [(q, corrupt_func(q, a)) for q, a in gsm8k_nshots[:n]]
    else:
        # 使用原始演示
        demos = gsm8k_nshots[:n]

    # 添加few-shot示例
    for q, a in demos:
        chats.append({"role": "user", "content": question_prompt(q)})
        chats.append({"role": "assistant", "content": answer_prompt(a)})

    # 添加当前问题
    chats.append({"role": "user", "content": question_prompt(question)})
    return chats


class QualityExperimentMethod(BaseMethod):
    """提示质量实验方法"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = LLMClient()
        self.corruption_type = config.get('corruption_type', None)
        self.corrupted_demos = config.get('corrupted_demos', None)
        self.n_examples = config.get('n_examples', 8)
        self.method_name = config.get('method_name', 'quality_experiment')
    
    def solve(self, question: str, ground_truth: Any = None) -> MethodResult:
        """解决单个问题"""
        start_time = time.time()
        
        try:
            # 构建被干扰的prompt
            messages = nshot_chats_corrupted(
                n=self.n_examples,
                question=question,
                corruption_type=self.corruption_type,
                corrupted_demos=self.corrupted_demos
            )
            
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

