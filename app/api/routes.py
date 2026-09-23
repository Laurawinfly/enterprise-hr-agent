"""HTTP API：给前端、Postman 或其他系统调用。"""
from fastapi import APIRouter, HTTPException
from app.schemas import ChatRequest, ChatResponse, ConfirmRequest
from app.agent.runtime import agent_runtime
from app.workflows.leave import leave_workflow

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        return agent_runtime.run(req.message, req.employee_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/workflows/leave/{workflow_id}/confirm")
def confirm(workflow_id: str, req: ConfirmRequest):
    try:
        return leave_workflow.confirm(workflow_id, req.employee_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/workflows/leave/{workflow_id}")
def status(workflow_id: str, employee_id: str = "E001"):
    try:
        return leave_workflow.status(workflow_id, employee_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
