# GSM8K 基线实现项目

## 项目概述
本项目实现了GSM8K数学推理任务的综合基线系统，包含多种提示方法、并发处理和高级混合策略。

## 项目架构

```
GSM8K 项目结构
├── data/                          # 数据层
│   ├── __init__.py
│   ├── config.py (配置文件)
│   ├── train.jsonl (训练数据)
│   └── test.jsonl (测试数据)
├── core/                          # 核心层
│   ├── __init__.py
│   ├── baseline.py (提示模板)
│   ├── llm_client.py (LLM API客户端)
│   └── evaluation.py (评估工具)
├── methods/                       # 方法层
│   ├── __init__.py
│   ├── base_method.py (基础方法接口)
│   ├── zero_shot_method.py (零样本方法)
│   ├── few_shot_method.py (少样本方法)
│   ├── progressive_hint_method.py (渐进提示方法)
│   ├── program_of_thoughts_method.py (程序思维方法)
│   └── hybrid_pot_php_method.py (混合PoT-PHP方法)
├── processing/                    # 处理层
│   ├── __init__.py
│   └── concurrent_processor.py (并发处理)
├── output/                        # 输出层
│   ├── results/ (原始结果)
│   │   ├── zeroshot.baseline.jsonl
│   │   ├── fewshot.baseline.jsonl
│   │   ├── progressive_hint.baseline.jsonl
│   │   ├── program_of_thoughts.baseline.jsonl
│   │   └── hybrid_pot_php.baseline.jsonl
│   └── summary/ (分析报告)
│       ├── zero-shot_temp0p1_topp0p9_*.json
│       ├── few-shot_temp0p1_topp0p9_*.json
│       ├── progressive-hint_temp0p3_topp0p9_*.json
│       ├── program-of-thoughts_temp0p1_topp0p9_*.json
│       └── hybrid-pot-php_temp0p1_topp0p9_*.json
├── main.py                        # 主执行脚本
├── README.md                      # 英文文档
├── README_CN.md                   # 中文文档
├── requirements.txt               # 依赖文件
└── assign.txt                     # 作业要求
```

## 项目状态

### ✅ 所有步骤已完成

#### **步骤1: 基础设施搭建** ✅
- ✅ 硅基流动API集成 (tencent/Hunyuan-MT-7B)
- ✅ 配置管理系统 (data/config.py)
- ✅ LLM客户端和错误处理 (core/llm_client.py)
- ✅ 依赖管理和项目结构 (requirements.txt)
- ✅ 主执行脚本框架 (main.py)

#### **步骤2: 核心功能实现** ✅
- ✅ 零样本和少样本提示模板 (core/baseline.py)
- ✅ 智能答案提取 (支持\boxed{}和####格式) (core/evaluation.py)
- ✅ Token统计和成本跟踪
- ✅ 批量处理框架
- ✅ 结果保存和评估

#### **步骤3: 模块化架构重构** ✅
- ✅ 分层目录结构 (data/core/methods/analysis/processing)
- ✅ 模块化方法设计 (BaseMethod接口)
- ✅ 插件化分析器 (BaseAnalyzer接口)
- ✅ 标准化数据格式 (MethodResult)
- ✅ 项目精简 (移除冗余文件)

#### **步骤4: 高级方法实现** ✅
- ✅ 渐进提示方法 (Progressive-Hint)
- ✅ 程序思维方法 (Program of Thoughts)
- ✅ 混合PoT-PHP策略
- ✅ 并发处理优化
- ✅ 进度跟踪和监控

#### **步骤5: 测试和优化** ✅
- ✅ 端到端测试通过
- ✅ 并发处理优化 (5个并发，1.07秒/问题)
- ✅ 完整功能验证
- ✅ 文档完善

## 已实现方法

### **基础方法**
- **零样本**: 无示例直接提示
- **少样本**: 使用8个示例的提示
- **并发处理**: 并行处理提升性能

### **高级方法**
- **渐进提示方法 (PHP)**: 多轮提示策略
  - 温度: 0.5 (创造性，生成多样化提示)
  - 少样本: 8个示例
  - 最大提示: 3轮
  - 准确率: ~53.5%

- **程序思维方法 (PoT)**: 代码生成和执行
  - 温度: 0.1 (精确性，代码生成要求准确)
  - 零样本: 直接生成代码
  - Python执行和错误处理
  - 准确率: ~40%

- **混合PoT-PHP**: 智能策略组合
  - PoT优先 (快速、精确)
  - PHP备用 (稳健、多轮)
  - 动态参数调整
  - 准确率: ~65.27%

## 技术配置

- **API服务商**: 硅基流动 - 兼容OpenAI API
- **模型**: tencent/Hunyuan-MT-7B
- **API端点**: https://api.siliconflow.cn/v1
- **温度**: 0.1 (默认)
- **Top-P**: 0.9
- **最大Token**: 2048
- **配置管理**: config.py
- **依赖管理**: pip + requirements.txt
- **并发处理**: asyncio + aiohttp

## 使用方法

### 基础使用
```bash
# 安装依赖
pip install -r requirements.txt

# 配置API密钥
# 编辑data/config.py中的OPENAI_API_KEY

# 运行所有方法
python main.py --method all

# 运行特定方法
python main.py --method zero-shot
python main.py --method few-shot
python main.py --method progressive-hint
python main.py --method program-of-thoughts
python main.py --method hybrid-pot-php

# 测试有限问题
python main.py --method hybrid-pot-php --max-questions 5 --verbose
```

### 高级使用
```bash
# 使用自定义参数运行
python main.py --method all --max-questions 200 --verbose

# 运行特定高级方法
python main.py --method progressive-hint --max-questions 50
python main.py --method program-of-thoughts --max-questions 50
python main.py --method hybrid-pot-php --max-questions 50
```

## 输出文件

### 原始结果
- `output/results/zeroshot.baseline.jsonl` - 零样本结果
- `output/results/fewshot.baseline.jsonl` - 少样本结果
- `output/results/progressive_hint.baseline.jsonl` - 渐进提示结果
- `output/results/program_of_thoughts.baseline.jsonl` - 程序思维结果
- `output/results/hybrid_pot_php.baseline.jsonl` - 混合方法结果

### 分析报告
- `output/summary/*_temp0p1_topp0p9_*.json` - 详细分析报告
- 包含准确率、处理时间、Token使用、成本估算

## 性能指标

### **方法对比**
| 方法 | 准确率 | 平均时间/问题 | Token使用 | 策略 |
|------|--------|---------------|-----------|------|
| 零样本 | 40% | 0.54秒 | 470 tokens | 直接提示 |
| 少样本 | 20% | 0.54秒 | 470 tokens | 基于示例 |
| 渐进提示 | 53.5% | 1.07秒 | 1168 tokens | 多轮提示 |
| 程序思维 | 40% | 1.68秒 | 379 tokens | 代码执行 |
| 混合PoT-PHP | 65.27% | 12.78秒 | 438 tokens | 智能回退 |

### **并发处理**
- **并发数**: 5-10个并行请求
- **速率限制**: 100-200请求/分钟
- **性能提升**: 3-5倍速度提升
- **错误处理**: 自动重试和指数退避

## 架构优势

- **模块化设计**: 清晰的分层结构
- **易于维护**: 相关功能集中管理
- **易于扩展**: 新方法可快速添加
- **高效**: 无冗余文件，结构清晰
- **并发处理**: 高性能并行执行
- **智能回退**: 混合策略获得最优结果

## 开发状态

### ✅ 已完成功能
- ✅ 所有基础提示方法
- ✅ 高级渐进提示方法
- ✅ 程序思维与代码执行
- ✅ 混合PoT-PHP策略
- ✅ 并发处理优化
- ✅ 进度跟踪和监控
- ✅ 全面错误处理
- ✅ Token使用和成本跟踪
- ✅ 详细分析报告

### 🚀 未来增强
- 更多混合策略
- 更高级的错误恢复
- 性能优化
- 扩展方法比较
