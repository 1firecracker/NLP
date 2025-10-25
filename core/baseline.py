

gsm8k_nshots = [
    (
        'There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?',
        'There are 15 trees originally. Then there were 21 trees after the Grove workers planted some more. So there must have been 21 - 15 = <<21-15=6>>6 trees that were planted.\n#### 6'
    ),
    (
        'If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?',
        'There are originally 3 cars. Then 2 more cars arrive. Now 3 + 2 = <<3+2=5>>5 cars are in the parking lot.\n#### 5'
    ),
    (
        'Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?',
        'Originally, Leah had 32 chocolates and her sister had 42. So in total they had 32 + 42 = <<32+42=74>>74. After eating 35, they had 74 - 35 = <<74-35=39>>39 pieces left in total.\n#### 39'
    ),
    (
        'Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?',
        'Jason had 20 lollipops originally. Then he had 12 after giving some to Denny. So he gave Denny 20 - 12 = <<20-12=8>>8 lollipops.\n#### 8'
    ),
    (
        'Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?',
        'Shawn started with 5 toys. He then got 2 toys each from his mom and dad. So he got 2 * 2 = <<2*2=4>>4 more toys. Now he has 5 + 4 = <<5+4=9>>9 toys.\n#### 9'
    ),
    (
        'There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?',
        'There were originally 9 computers. For each day from monday to thursday, 5 more computers were installed. So 4 * 5 = <<4*5=20>>20 computers were added. Now 9 + 20 = <<9+20=29>>29 computers are now in the server room.\n#### 29'
    ),
    (
        'Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?',
        'Michael started with 58 golf balls. He lost 23 on Tuesday, and lost 2 more on wednesday. So he had 58 - 23 = <<58-23=35>>35 at the end of Tuesday, and 35 - 2 = <<35-2=33>>33 at the end of wednesday.\n#### 33'
    ),
    (
        'Olivia has $23. She bought five bagels for $3 each. How much money does she have left?',
        'Olivia had 23 dollars. She bought 5 bagels for 3 dollars each. So she spent 5 * 3 = <<5*3=15>>15 dollars. Now she has 23 - 15 = <<23-15=8>>8 dollars left.\n#### 8'
    )
]


def nshot_chats(n: int, question: str) -> list:
    """
    构建n-shot prompting的对话格式
    
    Args:
        n: 示例数量 (0表示zero-shot)
        question: 当前问题
        
    Returns:
        list: 对话消息列表
    """
    def question_prompt(s):
        return f'Question: {s}'

    def answer_prompt(s):
        return f"Answer:\nLet's think step by step.\n{s}"

    chats = [
        {"role": "system", "content": f"Your task is to solve a series of math word problems by providing the final answer. Output format: #### integer . e.g.: #### 16 if the answer is 16"}
    ]

    # 添加few-shot示例
    for q, a in gsm8k_nshots[:n]:
        chats.append(
            {"role": "user", "content": question_prompt(q)})
        chats.append(
            {"role": "assistant", "content": answer_prompt(a)})

    # 添加当前问题
    chats.append({"role": "user", "content": question_prompt(question)})
    return chats


def call_llm_api(messages: list, client=None, **kwargs) -> tuple:
    """
    调用LLM API获取响应
    
    Args:
        messages: 对话消息列表
        client: LLM客户端实例
        **kwargs: 额外的生成参数
        
    Returns:
        tuple: (响应文本, token统计信息)
    """
    if client is None:
        from llm_client import LLMClient
        client = LLMClient()
    
    return client.generate_response(messages, **kwargs)

def get_zero_shot_prompt(question: str) -> list:
    """
    获取zero-shot prompt
    
    Args:
        question: 问题文本
        
    Returns:
        list: zero-shot对话消息
    """
    return nshot_chats(n=0, question=question)

def get_few_shot_prompt(question: str, n_examples: int = 8) -> list:
    """
    获取few-shot prompt
    
    Args:
        question: 问题文本
        n_examples: 示例数量
        
    Returns:
        list: few-shot对话消息
    """
    return nshot_chats(n=n_examples, question=question)

# 示例用法
if __name__ == "__main__":
    # 测试zero-shot
    test_question = "Elsa has 5 apples. Anna has 2 more apples than Elsa. How many apples do they have together?"
    
    zero_shot_prompt = get_zero_shot_prompt(test_question)
    print("Zero-shot prompt:")
    for msg in zero_shot_prompt:
        print(f"{msg['role']}: {msg['content'][:100]}...")
    
    # 测试few-shot
    few_shot_prompt = get_few_shot_prompt(test_question)
    print(f"\nFew-shot prompt (包含 {len(few_shot_prompt)} 条消息):")
    print(f"系统消息: {few_shot_prompt[0]['content']}")
    print(f"用户消息数量: {len([m for m in few_shot_prompt if m['role'] == 'user'])}")
    print(f"助手消息数量: {len([m for m in few_shot_prompt if m['role'] == 'assistant'])}")