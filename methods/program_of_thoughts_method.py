"""
Program of Thoughts (PoT) 方法实现
让LLM生成Python代码解决数学问题
"""
import time
import re
import subprocess
import tempfile
import os
from typing import List, Dict, Any
from methods.base_method import BaseMethod, MethodResult
from core.llm_client import LLMClient, token_tracker
from core.baseline import nshot_chats
from core.evaluation import extract_ans_from_response
from data.config import config

class ProgramOfThoughtsMethod(BaseMethod):
    """Program of Thoughts 方法"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = LLMClient()
        self.token_stats = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
        self.code_prompt = """Please solve this math problem by writing Python code.

Problem: {question}

Requirements:
1. Write Python code to solve the problem step by step
2. Use clear variable names and comments
3. Print the final answer at the end
4. Make sure the code is executable
5. Always define variables before using them

Python code:"""
    
    def solve(self, question: str, ground_truth: Any = None) -> MethodResult:
        """
        解决单个PoT问题
        
        Args:
            question: 问题文本
            ground_truth: 正确答案
            
        Returns:
            MethodResult: 方法结果
        """
        start_time = time.time()
        
        try:
            # 1. 生成Python代码
            code = self._generate_code(question)
            
            print("代码块内容:" + '\n'+ code)
            
            # 2. 执行代码
            execution_result = self._execute_code(code)
            
            # 3. 根据执行结果处理
            if execution_result["success"]:
                print("执行结果: " + '\n'+ execution_result["output"])
                predicted_answer = self._extract_answer_from_output(execution_result["output"])
                correct = (predicted_answer == ground_truth) if ground_truth else False
                result = execution_result["output"]
                error_info = None
            else:
                print("执行结果: " + '\n'+ f"Error: {execution_result['error']}")
                predicted_answer = None
                correct = False
                result = f"Execution failed: {execution_result['error']}"
                error_info = {
                    "error_message": execution_result["error"],
                    "error_type": self._classify_error(execution_result["error"]),
                    "failed_code": execution_result["code"],
                    "attempt_number": 1
                }
            
        except Exception as e:
            predicted_answer = None
            correct = False
            result = f"Error: {str(e)}"
            error_info = {
                "error_message": str(e),
                "error_type": "exception",
                "failed_code": None,
                "attempt_number": 1
            }
        
        processing_time = time.time() - start_time
        
        return MethodResult(
            method_name=self.method_name,
            question=question,
            ground_truth=ground_truth,
            predicted_answer=predicted_answer,
            response=result,
            token_stats=self.token_stats,  # 使用实际的token统计
            processing_time=processing_time,
            correct=correct,
            metadata={"error_info": error_info}  # 添加错误信息到metadata
        )
    
    def _generate_code(self, question: str) -> str:
        """生成Python代码（使用zero-shot）"""
        prompt = self.code_prompt.format(question=question)
        
        messages = [{"role": "user", "content": prompt}]
        
        response, token_stats = self.client.generate_response(messages)
        token_tracker.add_usage(token_stats)
        
        # 更新实例的token统计
        self.token_stats = token_stats
        
        # 提取代码块
        code = self._extract_code_from_response(response)
        
        return code
    
    def _extract_code_from_response(self, response: str) -> str:
        """从响应中提取Python代码"""
        # 查找代码块
        
        code_pattern = r'```python\s*(.*?)\s*```'
        
        match = re.search(code_pattern, response, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # 如果没有找到代码块，尝试查找其他格式
        lines = response.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if line.strip().startswith('def ') or line.strip().startswith('import ') or line.strip().startswith('from '):
                in_code = True
            if in_code:
                code_lines.append(line)
        
        return '\n'.join(code_lines) if code_lines else response
    
    def _execute_code(self, code: str) -> Dict[str, Any]:
        """执行Python代码，返回结构化结果"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # 执行代码
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 清理临时文件
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "error": None,
                    "code": code,
                    "execution_time": 0
                }
            else:
                return {
                    "success": False,
                    "output": result.stdout,
                    "error": result.stderr,
                    "code": code,
                    "execution_time": 0
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": None,
                "error": "Code execution timeout",
                "code": code,
                "execution_time": 30
            }
        except Exception as e:
            return {
                "success": False,
                "output": None,
                "error": str(e),
                "code": code,
                "execution_time": 0
            }
    
    def _classify_error(self, error_message: str) -> str:
        """分类错误类型，便于PHP处理"""
        if "SyntaxError" in error_message:
            return "syntax_error"
        elif "NameError" in error_message:
            return "name_error"
        elif "TypeError" in error_message:
            return "type_error"
        elif "ValueError" in error_message:
            return "value_error"
        elif "IndentationError" in error_message:
            return "indentation_error"
        elif "timeout" in error_message.lower():
            return "timeout_error"
        else:
            return "unknown_error"
    
    def _extract_answer_from_output(self, output: str) -> Any:
        """从代码输出中提取答案"""
        # 查找数字答案
        numbers = re.findall(r'-?\d+\.?\d*', output)
        if numbers:
            try:
                # 返回最后一个数字
                return float(numbers[-1]) if '.' in numbers[-1] else int(numbers[-1])
            except:
                pass
        
        # 查找特定格式的答案
        answer_patterns = [
            r'answer[:\s]*([-+]?\d*\.?\d+)',
            r'result[:\s]*([-+]?\d*\.?\d+)',
            r'final[:\s]*([-+]?\d*\.?\d+)'
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1)) if '.' in match.group(1) else int(match.group(1))
                except:
                    pass
        
        return None
    
    def batch_solve(self, questions: List[Dict[str, Any]]) -> List[MethodResult]:
        """
        批量解决PoT问题
        
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
