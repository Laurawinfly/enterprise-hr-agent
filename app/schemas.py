"""API 输入输出 Schema。Pydantic 会负责类型校验。"""
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    employee_id: str = "E001"  # Demo 中模拟登录用户；生产环境应从 SSO/JWT 获取。

class ChatResponse(BaseModel):
    answer: str
    trace: list[dict]

class ConfirmRequest(BaseModel):
    employee_id: str = "E001"
