from app.agent.runtime import AgentRuntime

def test_agent_balance_calls_tool():
    result = AgentRuntime().run("我还有多少年假？", "E001")
    assert "5 天" in result["answer"]
    assert any(x.get("tool") == "get_leave_balance" for x in result["trace"])

def test_agent_leave_stops_before_submit():
    # Agent 只能启动 Workflow，不能越过 Human Approval 自动提交。
    result = AgentRuntime().run("帮我请2026-10-01一天年假", "E001")
    assert "工作流编号" in result["answer"]
    tool_result = [x for x in result["trace"] if x["type"] == "tool_result"][0]["result"]
    assert tool_result["status"] == "WAITING_CONFIRMATION"
