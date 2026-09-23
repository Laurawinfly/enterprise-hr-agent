"""最小但真实的 Agent Loop。

默认使用可重复测试的 RuleBasedPlanner，保证没有 API Key 也能完整运行。
关键不是“规则比 LLM 强”，而是 Runtime 与 Planner 解耦：生产只需替换 Planner，
Tool、Workflow、权限、状态、Eval 不需要重写。
"""
import re
from dataclasses import dataclass
from datetime import date, timedelta
from app.tools.registry import execute_tool

@dataclass
class Decision:
    kind: str  # "tool" 或 "answer"
    name: str | None = None
    arguments: dict | None = None
    answer: str | None = None

class RuleBasedPlanner:
    """离线 Planner：用于教学、CI 和确定性 Eval。"""
    def decide(self, message: str, observations: list[dict]) -> Decision:
        if observations:
            obs = observations[-1]["result"]
            if obs.get("status") == "WAITING_CONFIRMATION":
                return Decision("answer", answer=(
                    f"已校验：申请 {obs['requested_days']} 天年假，当前余额 {obs['balance']} 天，"
                    f"审批人是 {obs['approver']}。工作流编号 {obs['workflow_id']}。"
                    "如要正式提交，请调用确认接口或回复确认并携带该编号。"))
            if obs.get("status") == "REJECTED":
                return Decision("answer", answer=f"无法继续申请：{obs['reason']}。")
            if "balance" in obs:
                return Decision("answer", answer=f"你当前还有 {obs['balance']} 天年假。")
            if "results" in obs:
                if not obs["results"]:
                    return Decision("answer", answer="知识库中没有检索到相关政策。")
                return Decision("answer", answer="根据公司知识库：" + obs["results"][0]["content"])
            if obs.get("status") == "COMPLETED":
                return Decision("answer", answer=f"请假已提交成功，申请单号：{obs['request_id']}。")

        if ("多少" in message and "年假" in message) or "年假余额" in message:
            return Decision("tool", "get_leave_balance", {})
        if any(k in message for k in ["政策", "规定", "病假", "婚假"]):
            return Decision("tool", "search_hr_policy", {"query": message})
        if "请" in message and "年假" in message:
            today = date.today()
            target = today + timedelta(days=1) if "明天" in message else today
            # 支持显式 YYYY-MM-DD，方便教学和自动化测试。
            m = re.search(r"(20\d{2}-\d{2}-\d{2})", message)
            if m:
                target = date.fromisoformat(m.group(1))
            return Decision("tool", "start_leave_request", {
                "leave_type": "annual",
                "start_date": target.isoformat(),
                "end_date": target.isoformat(),
            })
        return Decision("answer", answer="我可以查询年假余额、查询 HR 政策，或启动年假申请。")

class AgentRuntime:
    """负责反复执行“决策 → Tool → Observation”，直到模型给最终答案。"""
    def __init__(self, planner=None, max_steps: int = 5):
        self.planner = planner or RuleBasedPlanner()
        self.max_steps = max_steps

    def run(self, message: str, employee_id: str) -> dict:
        observations, trace = [], []
        for step in range(1, self.max_steps + 1):
            decision = self.planner.decide(message, observations)
            trace.append({"step": step, "type": "decision", "decision": decision.__dict__})
            if decision.kind == "answer":
                return {"answer": decision.answer, "trace": trace}

            result = execute_tool(decision.name, decision.arguments or {}, employee_id)
            trace.append({"step": step, "type": "tool_result", "tool": decision.name, "result": result})
            observations.append({"tool": decision.name, "result": result})

        # 防止模型/Planner 无限调用 Tool，是 Agent Runtime 的基础保护之一。
        return {"answer": "超过最大执行步数，已安全停止。", "trace": trace}

agent_runtime = AgentRuntime()
