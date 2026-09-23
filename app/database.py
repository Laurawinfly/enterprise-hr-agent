"""数据库基础设施。

教学重点：Workflow 的状态不能只放在 LLM 上下文里；它必须持久化。
为了让项目开箱即用，默认使用 SQLite。生产环境可把 DATABASE_URL 换成 PostgreSQL。
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hr_agent.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""
    pass
