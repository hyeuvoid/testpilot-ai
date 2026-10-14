from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select
from deepseek_client import generate_test_cases
from models import (
    HistoryDetail,
    HistoryListItem,
    TestCaseResponse,
)
from excel_exporter import build_test_case_excel
from document_parser import (
    DocumentParseError,
    extract_document_text,
)
from database import AnalysisHistory, SessionLocal, create_database
app = FastAPI(
    title="AI测试用例生成平台",
    description="分析软件需求并生成结构化测试用例",
    version="0.1.0",
)
create_database()
base_directory = Path(__file__).resolve().parent
frontend_directory = base_directory / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=frontend_directory),
    name="static",
)


class GenerateRequest(BaseModel):
    """前端发送的需求数据。"""

    requirement: str = Field(
        min_length=10,
        max_length=10000,
    )
class DocumentTextResponse(BaseModel):
    """文档文字提取结果。"""

    filename: str
    text: str
    character_count: int

@app.get("/", include_in_schema=False)
def home_page() -> FileResponse:
    """返回用户操作页面。"""

    return FileResponse(
        frontend_directory / "index.html"
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    """检查后端服务是否正常运行。"""

    return {
        "status": "ok",
        "message": "服务运行正常",
    }
@app.post(
    "/api/documents/extract",
    response_model=DocumentTextResponse,
)
async def extract_requirement_document(
    file: UploadFile = File(...),
) -> DocumentTextResponse:
    """接收需求文档并提取其中的文字。"""

    filename = file.filename or ""

    try:
        file_content = await file.read()

        extracted_text = extract_document_text(
            filename=filename,
            file_content=file_content,
        )

        return DocumentTextResponse(
            filename=filename,
            text=extracted_text,
            character_count=len(extracted_text),
        )

    except DocumentParseError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"读取文档失败：{error}",
        ) from error

    finally:
        await file.close()

@app.post(
    "/api/test-cases",
    response_model=TestCaseResponse,
)
def create_test_cases(
    request: GenerateRequest,
) -> TestCaseResponse:
    """接收软件需求、生成测试用例并保存历史记录。"""

    try:
        result = generate_test_cases(request.requirement)

        with SessionLocal() as database:
            history = AnalysisHistory(
                requirement=request.requirement,
                requirement_summary=result.requirement_summary,
                result_json=result.model_dump_json(),
                test_case_count=len(result.test_cases),
            )

            database.add(history)
            database.commit()

        return result

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"生成测试用例失败：{error}",
        ) from error
    """接收软件需求并生成测试用例。"""

    try:
        return generate_test_cases(request.requirement)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"生成测试用例失败：{error}",
        ) from error


@app.post("/api/export-excel")
def export_test_cases(
    result: TestCaseResponse,
) -> StreamingResponse:
    """把生成结果导出为 Excel 文件。"""

    try:
        excel_file = build_test_case_excel(result)

        return StreamingResponse(
            excel_file,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": (
                    'attachment; filename="testpilot-test-cases.xlsx"'
                )
            },
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"导出 Excel 失败：{error}",
        ) from error
@app.get(
    "/api/history",
    response_model=list[HistoryListItem],
)
def get_history() -> list[HistoryListItem]:
    """按照最新时间优先返回历史记录。"""

    with SessionLocal() as database:
        statement = select(AnalysisHistory).order_by(
            AnalysisHistory.created_at.desc()
        )

        records = database.scalars(statement).all()

        return [
            HistoryListItem(
                id=record.id,
                requirement=record.requirement,
                requirement_summary=record.requirement_summary,
                test_case_count=record.test_case_count,
                created_at=record.created_at,
            )
            for record in records
        ]


@app.get(
    "/api/history/{history_id}",
    response_model=HistoryDetail,
)
def get_history_detail(
    history_id: int,
) -> HistoryDetail:
    """根据编号返回一条完整的历史记录。"""

    with SessionLocal() as database:
        record = database.get(
            AnalysisHistory,
            history_id,
        )

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="没有找到这条历史记录",
            )

        result = TestCaseResponse.model_validate_json(
            record.result_json
        )

        return HistoryDetail(
            id=record.id,
            requirement=record.requirement,
            requirement_summary=record.requirement_summary,
            test_case_count=record.test_case_count,
            created_at=record.created_at,
            result=result,
        )