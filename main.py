import json

from deepseek_client import generate_test_cases


def main() -> None:
    requirement = """
    用户使用手机号和密码登录。
    手机号必须为11位数字。
    用户连续5次输入错误密码后，账号锁定30分钟。
    """

    print("正在分析需求并生成测试用例……")

    result = generate_test_cases(requirement)

    result_data = result.model_dump()

    print(
        json.dumps(
            result_data,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()