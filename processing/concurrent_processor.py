"""
并发API调用处理器
实现异步并发处理，提高3-5倍处理速度
"""
import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from data.config import config
from core.llm_client import LLMClient, token_tracker
from core.baseline import nshot_chats
from core.evaluation import extract_ans_from_response

@dataclass
class ProcessingResult:
    """处理结果数据类"""
    question: str
    ground_truth: Any
    predicted_answer: Any
    response: str
    token_stats: Dict[str, int]
    correct: bool
    processing_time: float
    error: Optional[str] = None

class ConcurrentProcessor:
    """并发API调用处理器"""
    
    def __init__(self, max_concurrent: int = 10, rate_limit: int = 100):
        """
        初始化并发处理器
        
        Args:
            max_concurrent: 最大并发数
            rate_limit: 每分钟请求限制
        """
        self.max_concurrent = max_concurrent
        self.rate_limit = rate_limit
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiter = RateLimiter(rate_limit)
        self.client = LLMClient()
        self.results = []
        self.start_time = None
        
    async def process_batch(self, 
                          questions: List[Dict[str, Any]], 
                          method: str = "zero-shot",
                          n_examples: int = 8) -> List[ProcessingResult]:
        """
        并发处理一批问题
        
        Args:
            questions: 问题列表
            method: 处理方法 (zero-shot, few-shot, tree-prompting)
            n_examples: few-shot示例数量
            
        Returns:
            List[ProcessingResult]: 处理结果列表
        """
        self.start_time = time.time()
        self.results = []
        
        print(f"🚀 开始并发处理 {len(questions)} 个问题 (方法: {method})")
        print(f"📊 并发设置: 最大并发数={self.max_concurrent}, 速率限制={self.rate_limit}/分钟")
        
        # 创建并发任务
        tasks = []
        for i, question_data in enumerate(questions):
            task = self._process_single_question(
                question_data, 
                method, 
                n_examples, 
                i + 1, 
                len(questions)
            )
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        valid_results = []
        for result in results:
            if isinstance(result, ProcessingResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                print(f"❌ 任务执行异常: {result}")
        
        processing_time = time.time() - self.start_time
        print(f"✅ 并发处理完成，总耗时: {processing_time:.2f}秒")
        print(f"📊 平均每个问题: {processing_time/len(questions):.2f}秒")
        
        return valid_results
    
    async def _process_single_question(self, 
                                    question_data: Dict[str, Any], 
                                    method: str,
                                    n_examples: int,
                                    current: int,
                                    total: int) -> ProcessingResult:
        """
        处理单个问题
        
        Args:
            question_data: 问题数据
            method: 处理方法
            n_examples: few-shot示例数量
            current: 当前问题编号
            total: 总问题数
            
        Returns:
            ProcessingResult: 处理结果
        """
        async with self.semaphore:
            try:
                # 速率限制
                await self.rate_limiter.wait_if_needed()
                
                start_time = time.time()
                question = question_data['question']
                ground_truth = extract_ans_from_response(question_data['answer'])
                
                # 构建prompt
                if method == "zero-shot":
                    messages = nshot_chats(n=0, question=question)
                elif method == "few-shot":
                    messages = nshot_chats(n=n_examples, question=question)
                elif method == "tree-prompting":
                    # TODO: 实现Tree Prompting
                    messages = nshot_chats(n=n_examples, question=question)
                else:
                    raise ValueError(f"未知的处理方法: {method}")
                
                # 调用API
                response, token_stats = await self._async_api_call(messages)
                
                # 提取答案
                predicted_answer = extract_ans_from_response(response)
                
                # 计算处理时间
                processing_time = time.time() - start_time
                
                # 更新token统计
                token_tracker.add_usage(token_stats)
                
                # 创建结果
                result = ProcessingResult(
                    question=question,
                    ground_truth=ground_truth,
                    predicted_answer=predicted_answer,
                    response=response,
                    token_stats=token_stats,
                    correct=predicted_answer == ground_truth,
                    processing_time=processing_time
                )
                
                if config.VERBOSE:
                    print(f"✅ 问题 {current}/{total}: 预测={predicted_answer}, 正确={ground_truth}, 正确={result.correct}")
                
                return result
                
            except Exception as e:
                print(f"❌ 处理问题 {current}/{total} 时出错: {e}")
                return ProcessingResult(
                    question=question_data['question'],
                    ground_truth=extract_ans_from_response(question_data['answer']),
                    predicted_answer=None,
                    response=None,
                    token_stats={},
                    correct=False,
                    processing_time=0,
                    error=str(e)
                )
    
    async def _async_api_call(self, messages: List[Dict[str, str]]) -> Tuple[str, Dict[str, int]]:
        """
        异步API调用
        
        Args:
            messages: 对话消息列表
            
        Returns:
            Tuple[str, Dict[str, int]]: (响应文本, token统计)
        """
        # 使用同步客户端进行异步调用
        loop = asyncio.get_event_loop()
        response, token_stats = await loop.run_in_executor(
            None, 
            self.client.generate_response, 
            messages
        )
        return response, token_stats

class RateLimiter:
    """API速率限制器"""
    
    def __init__(self, requests_per_minute: int = 60):
        """
        初始化速率限制器
        
        Args:
            requests_per_minute: 每分钟请求数限制
        """
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """检查是否需要等待以避免超过速率限制"""
        async with self.lock:
            now = time.time()
            
            # 清理1分钟前的请求记录
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            # 如果请求数超过限制，等待
            if len(self.requests) >= self.requests_per_minute:
                wait_time = 60 - (now - self.requests[0])
                if wait_time > 0:
                    print(f"⏳ 速率限制，等待 {wait_time:.2f} 秒...")
                    await asyncio.sleep(wait_time)
                    # 重新清理请求记录
                    now = time.time()
                    self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            # 记录当前请求
            self.requests.append(now)

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total: int):
        """
        初始化进度跟踪器
        
        Args:
            total: 总任务数
        """
        self.total = total
        self.completed = 0
        self.start_time = time.time()
        self.last_update = 0
    
    def update(self, increment: int = 1):
        """更新进度"""
        self.completed += increment
        now = time.time()
        
        # 每5秒或完成时更新一次
        if now - self.last_update >= 5 or self.completed >= self.total:
            self._print_progress()
            self.last_update = now
    
    def _print_progress(self):
        """打印进度信息"""
        elapsed = time.time() - self.start_time
        progress = self.completed / self.total
        eta = (elapsed / self.completed) * (self.total - self.completed) if self.completed > 0 else 0
        
        print(f"📊 进度: {self.completed}/{self.total} ({progress*100:.1f}%) - "
              f"耗时: {elapsed:.1f}s - 预计剩余: {eta:.1f}s")

# 全局进度跟踪器
progress_tracker = None

def get_progress_tracker(total: int) -> ProgressTracker:
    """获取全局进度跟踪器"""
    global progress_tracker
    if progress_tracker is None:
        progress_tracker = ProgressTracker(total)
    return progress_tracker
