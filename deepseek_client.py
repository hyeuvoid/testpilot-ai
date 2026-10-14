import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError
from models import TestCaseResponse

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL")
model = os.getenv("DEEPSEEK_MODEL")


def check_config() -> None:
    """检查DeepSeek的必要配置。"""
    missing_items = []

    if not api_key:
        missing_items.append("DEEPSEEK_API_KEY")

    if not base_url:
        missing_items.append("DEEPSEEK_BASE_URL")

    if not model:
        missing_items.append("DEEPSEEK_MODEL")

    if missing_items:
        missing_text = "、".join(missing_items)
        raise RuntimeError(f"缺少环境变量：{missing_text}")


def generate_test_cases(
    requirement: str,
) -> TestCaseResponse:
    """根据软件需求生成结构化测试用例。"""
    check_config()

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    system_prompt = """
    你是一名严谨的软件需求分析师和测试工程师。
    你的任务是分析用户提供的软件需求，并生成结构化测试用例。

    必须遵守以下规则：

    1. 将原始需求拆分成带编号的需求点。
    2. 不得把需求中没有明确说明的内容当作确定事实。
    3. 将描述不清楚、需要产品人员确认的内容放入ambiguities。
    4. 如果生成测试用例必须使用额外条件，把条件放入assumptions。
    5. 使用了额外假设的测试用例，based_on_assumption必须为true。
    6. 每条测试用例只验证一个主要场景。
    7. 不要自行编造页面跳转、按钮名称、提示文案或系统内部实现。
    8. 必须只返回合法JSON，不要输出Markdown或其他解释。
    """
    user_prompt = f"""
    请分析下面的软件需求：

    {requirement}

    请返回以下JSON结构：

    {{
      "requirement_summary": "需求概要",
      "requirement_points": [
        {{
          "requirement_id": "REQ_001",
          "description": "从原始需求中提取的需求点"
        }}
      ],
      "ambiguities": [
        "原始需求中描述不清楚、需要确认的问题"
      ],
      "assumptions": [
        "为了生成部分测试用例而采用的假设"
      ],
      "test_cases": [
        {{
          "case_id": "TC_LOGIN_001",
          "title": "测试用例名称",
          "related_requirement_ids": [
            "REQ_001"
          ],
          "preconditions": [
            "前置条件"
          ],
          "steps": [
            {{
              "step_number": 1,
              "action": "用户操作",
              "expected_result": "预期结果"
            }}
          ],
          "priority": "高、中或低",
          "test_type": "功能测试、异常测试或边界值测试",
          "based_on_assumption": false
        }}
      ]
    }}

    至少生成6条测试用例，并覆盖正常、异常和边界场景。
    如果没有歧义或假设，对应字段返回空数组。
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        response_format={
            "type": "json_object",
        },
        max_tokens=4000,
        extra_body={
            "thinking": {
                "type": "disabled",
            }
        },
        stream=False,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("DeepSeek没有返回有效内容")

    try:
        response_data = json.loads(content)
        return TestCaseResponse.model_validate(response_data)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"DeepSeek返回的内容不是合法JSON：{content}"
        ) from error

    except ValidationError as error:
        raise RuntimeError(
            f"DeepSeek返回的数据结构不符合要求：\n{error}"
        ) from error