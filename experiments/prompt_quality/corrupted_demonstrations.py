"""
演示干扰模块 - 创建不同质量水平的演示
"""
import random
import re
from typing import List, Tuple

# 导入原始演示
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.baseline import gsm8k_nshots


def corrupt_answer_only(question: str, answer: str) -> str:
    """
    只干扰答案，保持推理步骤正确
    
    Args:
        question: 问题文本
        answer: 原始答案
        
    Returns:
        被干扰的答案（答案错误，但推理步骤格式正确）
    """
    # 提取原始答案数字
    match = re.search(r'####\s*(\d+)', answer)
    if match:
        original_ans = int(match.group(1))
        # 生成一个错误的答案（±1-5的随机偏移）
        wrong_ans = original_ans + random.randint(-5, 5)
        if wrong_ans < 0:
            wrong_ans = abs(wrong_ans)
        if wrong_ans == original_ans:
            wrong_ans = original_ans + 1  # 确保答案不同
        # 替换答案
        corrupted = re.sub(r'####\s*\d+', f'#### {wrong_ans}', answer)
        return corrupted
    return answer


def corrupt_reasoning_only(question: str, answer: str) -> str:
    """
    只干扰推理步骤，答案可能碰巧正确
    
    Args:
        question: 问题文本
        answer: 原始答案
        
    Returns:
        被干扰的答案（推理步骤错误，但最终答案可能正确）
    """
    # 提取推理步骤中的计算
    # 例如：将 <<21-15=6>> 改为 <<21-15=7>>
    def corrupt_calculation(match):
        expr = match.group(1)
        result = match.group(2)
        # 尝试解析并修改
        try:
            # 简单处理：随机修改结果
            new_result = int(result) + random.randint(-3, 3)
            if new_result < 0:
                new_result = abs(new_result)
            return f"<<{expr}={new_result}>>"
        except:
            return match.group(0)
    
    corrupted = re.sub(r'<<([^=]+)=(\d+)>>', corrupt_calculation, answer)
    return corrupted


def corrupt_completely(question: str, answer: str) -> str:
    """
    完全干扰：推理和答案都错误
    
    Args:
        question: 问题文本
        answer: 原始答案
        
    Returns:
        完全错误的答案
    """
    # 先干扰推理
    corrupted = corrupt_reasoning_only(question, answer)
    # 再干扰答案
    corrupted = corrupt_answer_only(question, corrupted)
    return corrupted


def get_irrelevant_demonstrations():
    """
    获取不相关的演示（例如：代码生成示例）
    
    Returns:
        不相关的演示列表
    """
    return [
        (
            'Write a Python function to calculate factorial',
            'def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)\n#### def factorial(n):'
        ),
        (
            'How to reverse a string in Python?',
            'def reverse_string(s):\n    return s[::-1]\n#### return s[::-1]'
        ),
        (
            'What is the time complexity of binary search?',
            'Binary search has O(log n) time complexity because it divides the search space in half each iteration.\n#### O(log n)'
        ),
        (
            'Explain recursion in programming',
            'Recursion is when a function calls itself. It needs a base case to stop.\n#### base case'
        ),
        (
            'What is a hash table?',
            'A hash table is a data structure that maps keys to values using a hash function.\n#### hash function'
        ),
        (
            'How does quicksort work?',
            'Quicksort picks a pivot, partitions the array, and recursively sorts subarrays.\n#### pivot'
        ),
        (
            'What is object-oriented programming?',
            'OOP uses classes and objects to organize code. Key concepts include encapsulation and inheritance.\n#### classes'
        ),
        (
            'Explain the difference between stack and queue',
            'Stack is LIFO (Last In First Out), queue is FIFO (First In First Out).\n#### LIFO'
        ),
    ]


def get_partially_relevant_demonstrations():
    """
    获取部分相关的演示（数学题但类型不同）
    例如：用简单的算术题演示做复杂的应用题
    
    Returns:
        部分相关的演示列表
    """
    return [
        (
            'What is 2 + 2?',
            '2 + 2 = <<2+2=4>>4\n#### 4'
        ),
        (
            'Calculate 10 * 5',
            '10 * 5 = <<10*5=50>>50\n#### 50'
        ),
        (
            'What is 100 divided by 4?',
            '100 / 4 = <<100/4=25>>25\n#### 25'
        ),
        (
            'Subtract 15 from 30',
            '30 - 15 = <<30-15=15>>15\n#### 15'
        ),
        (
            'What is 3 squared?',
            '3^2 = <<3*3=9>>9\n#### 9'
        ),
        (
            'Calculate 7 + 8',
            '7 + 8 = <<7+8=15>>15\n#### 15'
        ),
        (
            'What is 20 - 6?',
            '20 - 6 = <<20-6=14>>14\n#### 14'
        ),
        (
            'Multiply 4 by 6',
            '4 * 6 = <<4*6=24>>24\n#### 24'
        ),
    ]


def get_mixed_demonstrations(relevant_ratio: float = 0.5):
    """
    获取混合演示（部分相关+部分不相关）
    
    Args:
        relevant_ratio: 相关演示的比例（0-1）
        
    Returns:
        混合演示列表
    """
    n_relevant = int(8 * relevant_ratio)
    n_irrelevant = 8 - n_relevant
    
    relevant = list(gsm8k_nshots[:n_relevant])
    irrelevant = get_irrelevant_demonstrations()[:n_irrelevant]
    
    # 随机混合
    mixed = relevant + irrelevant
    random.shuffle(mixed)
    return mixed[:8]


def get_format_inconsistent_demonstrations():
    """
    获取格式不一致的演示
    
    Returns:
        格式不一致的演示列表
    """
    inconsistent = []
    formats = [
        lambda a: f"Answer: {a}",  # 格式1：Answer: ...
        lambda a: f"答案是: {a}",  # 格式2：中文
        lambda a: f"The answer is {a}",  # 格式3：英文
        lambda a: a,  # 格式4：原始格式
    ]
    
    for i, (q, a) in enumerate(gsm8k_nshots):
        format_func = formats[i % len(formats)]
        # 提取答案部分
        answer_match = re.search(r'####\s*(\d+)', a)
        if answer_match:
            answer_num = answer_match.group(1)
            # 根据格式修改
            if i % len(formats) == 0:
                # Answer: 格式
                new_a = a.replace(f'#### {answer_num}', f'Answer: {answer_num}')
            elif i % len(formats) == 1:
                # 中文格式
                new_a = a.replace(f'#### {answer_num}', f'答案是: {answer_num}')
            elif i % len(formats) == 2:
                # 英文格式
                new_a = a.replace(f'#### {answer_num}', f'The answer is {answer_num}')
            else:
                new_a = a
            inconsistent.append((q, new_a))
        else:
            inconsistent.append((q, a))
    
    return inconsistent


def get_format_missing_demonstrations():
    """
    获取缺少关键格式的演示（没有####标记）
    
    Returns:
        缺少格式的演示列表
    """
    missing_format = []
    for q, a in gsm8k_nshots:
        # 移除####标记，但保留答案数字
        a_no_format = re.sub(r'####\s*(\d+)', r'\1', a).strip()
        missing_format.append((q, a_no_format))
    return missing_format


def get_format_chaotic_demonstrations():
    """
    获取格式混乱的演示（推理和答案混在一起）
    
    Returns:
        格式混乱的演示列表
    """
    chaotic = []
    for q, a in gsm8k_nshots:
        # 将答案混入推理步骤中，移除####标记
        answer_match = re.search(r'####\s*(\d+)', a)
        if answer_match:
            answer_num = answer_match.group(1)
            chaotic_answer = a.replace(f'\n#### {answer_num}', f' The final answer is {answer_num}.')
        else:
            chaotic_answer = a
        chaotic.append((q, chaotic_answer))
    return chaotic


# 演示干扰类型映射
CORRUPTION_TYPES = {
    'wrong_answer': corrupt_answer_only,
    'wrong_reasoning': corrupt_reasoning_only,
    'completely_wrong': corrupt_completely,
    'irrelevant': get_irrelevant_demonstrations,
    'partially_relevant': get_partially_relevant_demonstrations,
    'mixed_50_50': lambda: get_mixed_demonstrations(0.5),
    'format_inconsistent': get_format_inconsistent_demonstrations,
    'format_missing': get_format_missing_demonstrations,
    'format_chaotic': get_format_chaotic_demonstrations,
}


if __name__ == "__main__":
    # 测试各种干扰类型
    test_q, test_a = gsm8k_nshots[0]
    print("原始演示:")
    print(f"Q: {test_q}")
    print(f"A: {test_a}\n")
    
    print("错误答案:")
    print(corrupt_answer_only(test_q, test_a))
    print()
    
    print("错误推理:")
    print(corrupt_reasoning_only(test_q, test_a))
    print()
    
    print("完全错误:")
    print(corrupt_completely(test_q, test_a))

