"""Agent 可调用的 Tool Registry。

Tool 是面向 Agent 的业务能力，不等于把所有后端 API 原样暴露给模型。
"""
from app.services.hr_backend import hr_backend
from app.workflows.leave import leave_workflow
from app.rag.policy import search_policy

TOOL_SCHEMAS = [
    {"name": "get_leave_balance", "description": "查询当前登录员工的年假余额，不需要员工ID参数。", "parameters": {}},
    {"name": "start_leave_request", "description": "启动年假申请工作流，只启动并校验，不会直接正式提交。",
     "parameters": {"leave_type": "string", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}},
    {"name": "confirm_leave_request", "description": "用户明确确认后，继续已有请假工作流并正式提交。",
     "parameters": {"workflow_id": "string"}},
    {"name": "search_hr_policy", "description": "检索 HR 政策知识库。", "parameters": {"query": "string"}},
]

def execute_tool(name: str, arguments: dict, employee_id: str):
    # employee_id 来自 Agent Runtime 的可信上下文，而不是模型参数。
    if name == "get_leave_balance":
        return {"balance": hr_backend.get_leave_balance(employee_id), "unit": "days"}
    if name == "start_leave_request":
        return leave_workflow.start(employee_id=employee_id, **arguments)
    if name == "confirm_leave_request":
        return leave_workflow.confirm(employee_id=employee_id, **arguments)
    if name == "search_hr_policy":
        return {"results": search_policy(arguments["query"])}
    raise ValueError(f"未知 Tool: {name}")
