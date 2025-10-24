"""
GSM8K Baseline 配置文件
"""
import os
from typing import Optional

class Config:
    """配置管理类"""
    
    # 硅基流动 API 配置 (兼容OpenAI API)
    OPENAI_API_KEY: str = "sk-ulfbgpjfvziuiaeuqhmuxskxdosfqilzookvutbonnhpeycw"  # 硅基流动API密钥
    OPENAI_MODEL: str = "tencent/Hunyuan-MT-7B"  # 硅基流动模型
    OPENAI_BASE_URL: Optional[str] = "https://api.siliconflow.cn/v1"  # 硅基流动API端点
    
    # 推理参数
    TEMPERATURE: float = 0.1
    TOP_P: float = 0.9
    MAX_TOKENS: int = 2048
    FREQUENCY_PENALTY: float = 0.0
    PRESENCE_PENALTY: float = 0.0
    
    # 文件路径配置
    TRAIN_FILE: str = "data/train.jsonl"
    TEST_FILE: str = "data/test.jsonl"
    OUTPUT_DIR: str = "output/results"
    
    # 批处理配置
    BATCH_SIZE: int = 10
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    VERBOSE: bool = True
    
    @classmethod
    def load_from_env(cls):
        """从环境变量加载配置"""
        cls.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", cls.OPENAI_API_KEY)
        cls.OPENAI_MODEL = os.getenv("OPENAI_MODEL", cls.OPENAI_MODEL)
        cls.TEMPERATURE = float(os.getenv("TEMPERATURE", cls.TEMPERATURE))
        cls.TOP_P = float(os.getenv("TOP_P", cls.TOP_P))
        cls.MAX_TOKENS = int(os.getenv("MAX_TOKENS", cls.MAX_TOKENS))
        cls.BATCH_SIZE = int(os.getenv("BATCH_SIZE", cls.BATCH_SIZE))
        cls.LOG_LEVEL = os.getenv("LOG_LEVEL", cls.LOG_LEVEL)
        cls.VERBOSE = os.getenv("VERBOSE", "true").lower() == "true"
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否有效"""
        if cls.OPENAI_API_KEY == "your_openai_api_key_here":
            print("⚠️  警告: 请设置有效的OpenAI API密钥")
            return False
        return True
    
    @classmethod
    def print_config(cls):
        """打印当前配置"""
        print("📋 当前配置:")
        print(f"  - 模型: {cls.OPENAI_MODEL}")
        print(f"  - Temperature: {cls.TEMPERATURE}")
        print(f"  - Top-P: {cls.TOP_P}")
        print(f"  - Max Tokens: {cls.MAX_TOKENS}")
        print(f"  - Batch Size: {cls.BATCH_SIZE}")
        print(f"  - 输出目录: {cls.OUTPUT_DIR}")

# 全局配置实例
config = Config()
