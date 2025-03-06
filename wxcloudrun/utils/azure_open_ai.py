import os
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-08-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

ASSISTANT_ID = "asst_E2lg4wmbBxAAuAjQG2bZ1xLw"  # 情绪分析助手


def chat_with_assistant(user_input: str):
    res = _chat_with_assistant(user_input)
    if len(res) == 3:
        return res
    elif isinstance(res, list):
        res = res[0].split('，')
        return [res[0], res[1].strip(), ','.join(res[2:])]
    else:
        return ['未知分类', 3, '继续加油吧']


def _chat_with_assistant(user_input: str):
    """
    使用 Azure OpenAI Assistant 进行对话
    :param user_input: 用户输入的文本
    :return: AI 助手的回复
    """
    # 创建一个对话线程
    thread = client.beta.threads.create()

    # 在线程中添加用户消息
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    # 运行 Assistant 处理消息
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    # 轮询等待 Assistant 运行完成
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status in ["completed", "failed", "cancelled"]:
            break

    if run_status.status == "completed":
        # 获取 AI 回复
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for message in messages.data:
            if message.role == "assistant":
                return message.content[0].text.value.replace("(", "").replace(")", "").split(',')  # 获取 AI 回复的文本

    raise Exception("AI 助手无法生成回复，请稍后再试。")


if __name__ == '__main__':
    res = chat_with_assistant("测试")
    print(res)
    (category, positive, comment) = res
    positive = int(positive.strip())
    print(category, positive, comment)
