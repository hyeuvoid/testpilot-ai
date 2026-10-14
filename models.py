from typing import Literal

from pydantic import BaseModel, Field
from datetime import datetime

class RequirementPoint(BaseModel):
    """从原始需求中提取出的需求点。"""

    requirement_id: str = Field(
        pattern=r"^REQ_\d{3}$"
    )
    description: str = Field(min_length=1)


class TestStep(BaseModel):
    """测试用例中的单个操作步骤。"""

    step_number: int = Field(ge=1)
    action: str = Field(min_length=1)
    expected_result: str = Field(min_length=1)


class TestCase(BaseModel):
    """一条完整的测试用例。"""

    case_id: str = Field(
        pattern=r"^TC_[A-Z0-9_]+$"
    )
    title: str = Field(min_length=1)
    related_requirement_ids: list[str] = Field(
        min_length=1
    )
    preconditions: list[str]
    steps: list[TestStep] = Field(min_length=1)
    priority: Literal["高", "中", "低"]
    test_type: Literal[
        "功能测试",
        "异常测试",
        "边界值测试",
    ]
    based_on_assumption: bool


class TestCaseResponse(BaseModel):
    """DeepSeek返回的完整数据结构。"""

    requirement_summary: str = Field(min_length=1)
    requirement_points: list[RequirementPoint] = Field(
        min_length=1
    )
    ambiguities: list[str]
    assumptions: list[str]
    test_cases: list[TestCase] = Field(min_length=1)
class HistoryListItem(BaseModel):
    """历史记录列表中的一项。"""

    id: int
    requirement: str
    requirement_summary: str
    test_case_count: int
    created_at: datetime


class HistoryDetail(HistoryListItem):
    """一条历史记录的完整内容。"""

    result: TestCaseResponse