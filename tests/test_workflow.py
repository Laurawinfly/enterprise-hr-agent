from app.workflows.leave import leave_workflow

def test_leave_workflow_requires_confirmation_and_is_idempotent():
    started = leave_workflow.start("E001", "annual", "2026-10-01", "2026-10-01")
    assert started["status"] == "WAITING_CONFIRMATION"

    first = leave_workflow.confirm(started["workflow_id"], "E001")
    second = leave_workflow.confirm(started["workflow_id"], "E001")

    assert first["status"] == "COMPLETED"
    assert second["request_id"] == first["request_id"]
    assert second["idempotent"] is True

def test_insufficient_balance_is_rejected():
    result = leave_workflow.start("E002", "annual", "2026-10-01", "2026-10-03")
    assert result["status"] == "REJECTED"
    assert result["reason"] == "年假余额不足"
