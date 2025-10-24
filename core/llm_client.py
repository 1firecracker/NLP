"""
OpenAI API 客户端
"""
import time
import json
from typing import List, Dict, Any, Optional, Tuple
import openai
from openai import OpenAI
from data.config import config

class LLMClient:
    """OpenAI API客户端"""
    
    def __init__(self):
        """初始化客户端"""
        # 支持硅基流动API端点
        if config.OPENAI_BASE_URL:
            self.client = OpenAI(
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_BASE_URL
            )
        else:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        self.model = config.OPENAI_MODEL
        self.max_retries = config.MAX_RETRIES
        self.retry_delay = config.RETRY_DELAY
        
    def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> Tuple[str, Dict[str, int]]:
        """
        生成响应
        
        Args:
            messages: 对话消息列表
            **kwargs: 额外的生成参数
            
        Returns:
            Tuple[str, Dict[str, int]]: (响应文本, token统计信息)
        """
        # 设置生成参数
        generation_params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", config.TEMPERATURE),
            "top_p": kwargs.get("top_p", config.TOP_P),
            "max_tokens": kwargs.get("max_tokens", config.MAX_TOKENS),
            "frequency_penalty": kwargs.get("frequency_penalty", config.FREQUENCY_PENALTY),
            "presence_penalty": kwargs.get("presence_penalty", config.PRESENCE_PENALTY),
        }
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**generation_params)
                
                # 提取响应内容
                response_text = response.choices[0].message.content
                
                # 统计token使用量
                token_stats = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                
                if config.VERBOSE:
                    print(f"✅ API调用成功 (尝试 {attempt + 1}/{self.max_retries})")
                    print(f"📊 Token使用: {token_stats['total_tokens']} (输入: {token_stats['prompt_tokens']}, 输出: {token_stats['completion_tokens']})")
                
                return response_text, token_stats
                
            except openai.RateLimitError as e:
                print(f"⚠️  API限流错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                    print(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise e
                    
            except openai.APIError as e:
                print(f"❌ API错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise e
                    
            except Exception as e:
                print(f"❌ 未知错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise e
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        try:
            # 使用tiktoken进行token计数
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except ImportError:
            # 如果没有tiktoken，使用简单估算
            return len(text.split()) * 1.3  # 粗略估算
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            test_messages = [
                {"role": "user", "content": "Hello, this is a test message."}
            ]
            response, _ = self.generate_response(test_messages, max_tokens=10)
            print("✅ API连接测试成功")
            return True
        except Exception as e:
            print(f"❌ API连接测试失败: {e}")
            return False

class TokenTracker:
    """Token使用量跟踪器"""
    
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.api_calls = 0
        
    def add_usage(self, token_stats: Dict[str, int]):
        """添加token使用统计"""
        self.total_prompt_tokens += token_stats.get("prompt_tokens", 0)
        self.total_completion_tokens += token_stats.get("completion_tokens", 0)
        self.total_tokens += token_stats.get("total_tokens", 0)
        self.api_calls += 1
        
    def get_summary(self) -> Dict[str, Any]:
        """获取使用统计摘要"""
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "api_calls": self.api_calls,
            "average_tokens_per_call": self.total_tokens / max(self.api_calls, 1)
        }
    
    def print_summary(self):
        """打印使用统计"""
        summary = self.get_summary()
        print("\n📊 Token使用统计:")
        print(f"  - 总API调用次数: {summary['api_calls']}")
        print(f"  - 总输入Token: {summary['total_prompt_tokens']}")
        print(f"  - 总输出Token: {summary['total_completion_tokens']}")
        print(f"  - 总Token使用: {summary['total_tokens']}")
        print(f"  - 平均每次调用Token: {summary['average_tokens_per_call']:.1f}")

# 全局token跟踪器
token_tracker = TokenTracker()
