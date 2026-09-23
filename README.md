# Enterprise HR Agent V8 — Security, Governance & Harness

一个用于学习和演示**企业级 Agent 如何真正接入业务系统**的完整 HR Agent 后端。项目从 LLM Tool Calling 出发，把 Conversation/State、Workflow、MCP、RAG、Eval 与 Harness 安全治理组合到同一条可运行链路中。

## 总体架构

```text
Client -> FastAPI Agent API
       -> Conversation / Context
       -> Harness (RBAC / Audit / Timeout / Redaction)
       -> Agent Runtime
       -> Tool Transport (Local or MCP)
       -> Workflow / RAG
       -> Mock HR System
```

核心边界：**LLM 决定想做什么；Harness 决定允不允许；Workflow 决定业务能否继续；Backend 决定真实数据是什么。**

## 目录

```text
app/agent/          Agent Loop、Rule/LLM Runtime
app/conversation/   服务端会话历史
app/context/        Context Builder / Active Workflow
app/governance/     Audit、Timeout、Retry
app/llm/            多模型 OpenAI-compatible adapter
app/mcp_client/     MCP client adapter
app/mcp_server/     HR MCP Server
app/rag/            Chunk、Embedding、pgvector、Hybrid Retrieval
app/security/       AuthContext、RBAC、脱敏、Injection signal
app/services/       HR backend client
app/tools/          Tool registry / ToolTransport
app/workflows/      确定性请假状态机
mock_hr_system/     独立 Mock 企业 HR 系统
evals/              Agent/RAG/Security evaluation
tests/              单元/集成测试
```

## 零 Key 运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn mock_hr_system.main:app --reload --port 8001
```

另一个终端：

```bash
export MODEL_PROVIDER=rule
export TOOL_TRANSPORT=local
export HR_BACKEND_MODE=http
export HR_BACKEND_URL=http://127.0.0.1:8001
uvicorn app.main:app --reload --port 8000
```

访问 `http://127.0.0.1:8000/docs`。先 POST `/api/chat` 创建请假，再携带返回的 `conversation_id` 只说“确认”；服务端会从 Active Workflow 找到真实 workflow_id。

## LLM / MCP / RAG

LLM 可通过环境变量选择 OpenAI、DeepSeek 或 OpenAI-compatible provider。API Key 只放环境变量。

Tool Transport 可选 `local` 或 `mcp`。MCP 模式链路为：

```text
Agent -> MCP Client -> list_tools/call_tool -> HR MCP Server -> Workflow/API
```

RAG 默认 `RAG_BACKEND=keyword`。pgvector 实验：

```bash
docker compose -f docker-compose.rag.yml up -d
export RAG_BACKEND=pgvector
export EMBEDDING_PROVIDER=local_hash
python scripts/index_policies.py
python -m evals.rag_runner
```

`local_hash` 只用于 deterministic 测试，不代表生产语义质量。

## Docker

```bash
docker compose up --build
```

启动 Agent API :8000 和 Mock HR :8001。pgvector 使用 `docker-compose.rag.yml`。

## 测试

```bash
pytest -q
python -m evals.runner_v5 --provider rule
python -m evals.security_runner
python -m evals.rag_runner
```

V8 hardening 已实际执行：**22 passed**。

真实 OpenAI/DeepSeek API、MCP 网络服务和 PostgreSQL/pgvector 需要对应外部依赖/API Key 后再做 live integration test；离线单测不冒充这些外部链路已经验证。

## 安全

- AuthContext 身份来自可信 Runtime，不来自模型参数。
- Tool 执行前代码级 RBAC。
- 请假 Workflow 必须停在 WAITING_CONFIRMATION。
- confirm 时使用服务端 Active Workflow，覆盖模型幻觉 workflow_id。
- Tool authorize/start/success/failure 有审计 hook。
- Trace/Audit 基础 PII/secret 脱敏。
- Tool 调用 timeout/retry。
- Prompt-injection heuristic 只是 defense-in-depth，不是完整安全方案。

生产仍需真实 JWT/SSO 验签、数据库 tenant/RLS、Secrets Manager、持久化 Audit Store、OpenTelemetry、限流与正式 DLP。

## 版本

V1 Minimal Agent → V2 Mock HR → V3 Multi-LLM → V4 Context/State → V5 Eval → V6 MCP → V7 RAG → **V8 Security/Governance/Harness**。
