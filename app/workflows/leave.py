"""请假 Workflow：把确定性的业务规则从 LLM 决策空间中移出来。"""
from datetime import date
from uuid import uuid4
from sqlalchemy import select
from app.database import SessionLocal
from app.models import LeaveWorkflow, WorkflowEvent
from app.services.hr_backend import hr_backend

class LeaveWorkflowService:
    def _days(self, start_date: str, end_date: str) -> int:
        start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
        if end < start:
            raise ValueError("结束日期不能早于开始日期")
        # Demo 按自然日计算；生产系统应接入企业工作日历/节假日规则。
        return (end - start).days + 1

    def start(self, employee_id: str, leave_type: str, start_date: str, end_date: str) -> dict:
        duration = self._days(start_date, end_date)
        balance = hr_backend.get_leave_balance(employee_id)
        if leave_type != "annual":
            return {"status": "REJECTED", "reason": "Demo 仅实现年假流程"}
        if balance < duration:
            return {"status": "REJECTED", "reason": "年假余额不足", "balance": balance, "requested_days": duration}

        workflow_id = str(uuid4())
        approver = hr_backend.get_approver(employee_id)
        with SessionLocal() as db:
            wf = LeaveWorkflow(id=workflow_id, employee_id=employee_id,
                status="WAITING_CONFIRMATION", leave_type=leave_type,
                start_date=start_date, end_date=end_date, duration=duration, approver=approver)
            db.add(wf)
            db.add(WorkflowEvent(workflow_id=workflow_id, event_type="WORKFLOW_STARTED",
                                 detail=f"余额={balance}; 天数={duration}; 审批人={approver}"))
            db.commit()
        return {"workflow_id": workflow_id, "status": "WAITING_CONFIRMATION",
                "balance": balance, "requested_days": duration, "approver": approver,
                "start_date": start_date, "end_date": end_date}

    def confirm(self, workflow_id: str, employee_id: str) -> dict:
        with SessionLocal() as db:
            wf = db.scalar(select(LeaveWorkflow).where(LeaveWorkflow.id == workflow_id))
            if not wf or wf.employee_id != employee_id:
                raise ValueError("工作流不存在或无权访问")
            # 已完成时直接返回第一次结果，保证重复确认幂等。
            if wf.status == "COMPLETED":
                return {"workflow_id": wf.id, "status": wf.status,
                        "request_id": wf.external_request_id, "idempotent": True}
            if wf.status != "WAITING_CONFIRMATION":
                raise ValueError(f"当前状态 {wf.status} 不允许确认")
            wf.status = "SUBMITTING"
            db.add(WorkflowEvent(workflow_id=wf.id, event_type="USER_CONFIRMED", detail="用户明确确认提交"))
            db.commit()

            result = hr_backend.create_leave_request(employee_id=employee_id, workflow_id=wf.id,
                leave_type=wf.leave_type, start_date=wf.start_date, end_date=wf.end_date)
            wf.status = "COMPLETED"
            wf.external_request_id = result["request_id"]
            db.add(WorkflowEvent(workflow_id=wf.id, event_type="WORKFLOW_COMPLETED", detail=result["request_id"]))
            db.commit()
            return {"workflow_id": wf.id, "status": wf.status, "request_id": wf.external_request_id}

    def status(self, workflow_id: str, employee_id: str) -> dict:
        with SessionLocal() as db:
            wf = db.scalar(select(LeaveWorkflow).where(LeaveWorkflow.id == workflow_id))
            if not wf or wf.employee_id != employee_id:
                raise ValueError("工作流不存在或无权访问")
            return {"workflow_id": wf.id, "status": wf.status, "start_date": wf.start_date,
                    "end_date": wf.end_date, "approver": wf.approver, "request_id": wf.external_request_id}

leave_workflow = LeaveWorkflowService()
