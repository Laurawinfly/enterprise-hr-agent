from app.rag.policy import search_policy

def test_policy_search_returns_evidence():
    results = search_policy("年假申请有什么规定？")
    assert results
    assert "明确确认" in results[0]["content"]
    assert results[0]["source"] == "data/hr_policies.md"
