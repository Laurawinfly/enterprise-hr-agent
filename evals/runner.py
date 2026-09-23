"""最小 Eval Runner：真实执行 Agent，并统计 Tool Selection Accuracy。"""
import json
from pathlib import Path
from app.agent.runtime import AgentRuntime
from app.database import Base, engine

DATASET = Path(__file__).with_name("dataset.json")

def run_eval():
    # Eval 可能独立运行，因此主动初始化持久化表。
    Base.metadata.create_all(bind=engine)
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    agent, correct, rows = AgentRuntime(), 0, []

    for case in cases:
        result = agent.run(case["input"], case["employee_id"])
        calls = [x["tool"] for x in result["trace"] if x["type"] == "tool_result"]
        actual = calls[0] if calls else None
        ok = actual == case["expected_tool"]
        correct += int(ok)
        rows.append({
            "input": case["input"],
            "expected": case["expected_tool"],
            "actual": actual,
            "ok": ok,
        })

    report = {
        "cases": len(cases),
        "tool_selection_accuracy": correct / len(cases),
        "details": rows,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report

if __name__ == "__main__":
    run_eval()
