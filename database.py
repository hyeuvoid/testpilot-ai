from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


DATABASE_URL = "sqlite:///./testpilot.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)
def utc_now() -> datetime:
    """返回适合 SQLite 保存的 UTC 时间。"""

    return datetime.now(
        timezone.utc
    ).replace(tzinfo=None)

class Base(DeclarativeBase):
    """所有数据库表模型的基础类。"""

    pass


class AnalysisHistory(Base):
    """保存每次需求分析的历史记录。"""

    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    requirement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    requirement_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    result_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    test_case_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


def create_database() -> None:
    """创建尚不存在的数据库表。"""

    Base.metadata.create_all(bind=engine)