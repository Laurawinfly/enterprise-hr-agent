import os
os.environ["DATABASE_URL"] = "sqlite:///./test_hr_agent.db"

import pytest
from app.database import Base, engine
from app.services.hr_backend import _CREATED

@pytest.fixture(autouse=True)
def clean_db():
    """每条测试前重建数据库，保证测试互不污染、结果可重复。"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    _CREATED.clear()
    yield
