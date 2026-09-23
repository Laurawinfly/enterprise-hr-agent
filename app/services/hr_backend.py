"""模拟企业 HR 后端。

真实项目中，这一层应调用北森/用友/Workday/SAP/OA 等 API。
Agent 不应该直接操作数据库业务表，而应通过稳定的 Service/Tool 边界访问。
"""
from datetime import date

EMPLOYEES = {
    "E001": {"name": "小燕", "annual_leave_balance": 5, "approver": "王明"},
    "E002": {"name": "小李", "annual_leave_balance": 1, "approver": "赵敏"},
}
_CREATED: dict[str, dict] = {}

class HRBackend:
    def get_employee(self, employee_id: str) -> dict:
        if employee_id not in EMPLOYEES:
            raise ValueError("员工不存在")
        return EMPLOYEES[employee_id]

    def get_leave_balance(self, employee_id: str) -> int:
        return int(self.get_employee(employee_id)["annual_leave_balance"])

    def get_approver(self, employee_id: str) -> str:
        return str(self.get_employee(employee_id)["approver"])

    def create_leave_request(self, *, employee_id: str, workflow_id: str,
                             leave_type: str, start_date: str, end_date: str) -> dict:
        """使用 workflow_id 做幂等键，防止用户连续点击两次确认产生两张单。"""
        if workflow_id in _CREATED:
            return _CREATED[workflow_id]
        result = {
            "request_id": f"LV-{len(_CREATED)+1:04d}",
            "employee_id": employee_id,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "created_on": date.today().isoformat(),
            "status": "SUBMITTED",
        }
        _CREATED[workflow_id] = result
        return result

hr_backend = HRBackend()
