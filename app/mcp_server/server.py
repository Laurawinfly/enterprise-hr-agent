"""MCP Server：把 HR 能力以标准 MCP Tool 暴露给外部 Agent。

基于 MCP Python SDK v2 的 MCPServer API。
注意：Demo 用 employee_id 参数模拟认证上下文；生产应通过 MCP Auth/网关注入身份。
"""
from mcp.server import MCPServer
from app.services.hr_backend import hr_backend
from app.workflows.leave import leave_workflow
from app.rag.policy import search_policy

mcp = MCPServer("Enterprise HR MCP")

@mcp.tool()
def get_leave_balance(employee_id: str = "E001") -> dict:
    """查询员工年假余额。"""
    return {"balance": hr_backend.get_leave_balance(employee_id), "unit": "days"}

@mcp.tool()
def start_leave_request(start_date: str, end_date: str,
                        leave_type: str = "annual", employee_id: str = "E001") -> dict:
    """启动请假工作流；正式提交前会停在 WAITING_CONFIRMATION。"""
    return leave_workflow.start(employee_id, leave_type, start_date, end_date)

@mcp.tool()
def confirm_leave_request(workflow_id: str, employee_id: str = "E001") -> dict:
    """用户明确确认后正式提交已有请假工作流。"""
    return leave_workflow.confirm(workflow_id, employee_id)

@mcp.tool()
def search_hr_policy(query: str) -> dict:
    """检索 HR 政策知识库。"""
    return {"results": search_policy(query)}
