# Enterprise HR Agent｜企业级 HR Agent 可运行教学项目

这是《企业级 Agent 架构与落地实战》的配套源码。它不是只展示 Prompt 的 Demo，而是把 **Agent Loop、Tool、Workflow、持久化状态、Human Approval、幂等、RAG、MCP、Trace、Eval、API** 串成一条可以运行和测试的完整链路。

> 设计原则：不把确定性业务规则交给 LLM。LLM/Planner 负责理解与选择能力；余额校验、状态机、正式提交、权限边界、幂等由代码和 Workflow 控制。

## 架构

```text
用户 → FastAPI /chat → Agent Runtime → Planner → Tool Registry
                                      ├─ get_leave_balance → Mock HR Backend
                                      ├─ search_hr_policy → Policy Retrieval
                                      └─ start_leave_request → Leave Workflow
                                                              ↓
                                                        状态持久化
                                                              ↓
                                                   WAITING_CONFIRMATION
                                                              ↓
                                                        用户明确确认
                                                              ↓
                                                         HR Backend
                                                              ↓
                                                          COMPLETED
```

同一组企业能力还通过 MCP Server 暴露给外部 Agent / MCP Client。

## 技术栈

- Python 3.12（3.10+ 可用）
- FastAPI
- SQLAlchemy
- SQLite（默认零配置；生产可换 PostgreSQL）
- Pydantic
- MCP Python SDK v2
- pytest
- Docker / Docker Compose
- 自研最小 Agent Runtime

## 为什么默认不用真实 LLM API？

项目默认提供 `RuleBasedPlanner`：无需 API Key 即可完整运行、测试结果可重复，并把 Agent Runtime、Tool、Workflow 与模型厂商解耦。它仍运行真实的 **Decision → Tool Call → Observation → Decision** Agent Loop。生产接入 LLM 时，只需替换 Planner/Model Adapter。

## 目录结构

```text
enterprise-hr-agent/
├── app/
│   ├── agent/runtime.py
│   ├── api/routes.py
│   ├── mcp_server/server.py
│   ├── rag/policy.py
│   ├── services/hr_backend.py
│   ├── tools/registry.py
│   ├── workflows/leave.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── main.py
├── data/hr_policies.md
├── evals/
│   ├── dataset.json
│   ├── latest_report.json
│   └── runner.py
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

源码包含详细中文注释，重点解释“为什么这样设计”。

## 本地启动

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

打开 Swagger：`http://127.0.0.1:8000/docs`，健康检查：`http://127.0.0.1:8000/health`。

也可以：

```bash
docker compose up --build
```

## 第一个 Agent 请求

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"我还有多少年假？","employee_id":"E001"}'
```

响应包含 `trace`，可以观察 Decision、Tool Call 与 Tool Result。

## 完整请假流程

启动：

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"帮我请2026-10-01一天年假","employee_id":"E001"}'
```

Workflow 完成日期校验、余额查询、确定性余额规则、审批人查询，然后停在 `WAITING_CONFIRMATION`，不会直接提交。

确认：

```bash
curl -X POST http://127.0.0.1:8000/api/workflows/leave/<workflow_id>/confirm \
  -H 'Content-Type: application/json' \
  -d '{"employee_id":"E001"}'
```

确认后进入 `COMPLETED` 并生成 `LV-xxxx` 申请单号。重复确认不会生成第二张单：`workflow_id` 同时作为 Mock HR Backend 的幂等键。

## 安全边界

Demo 为方便演示允许传 `employee_id`。生产环境必须改成：

```text
SSO / OAuth / JWT → API Gateway → Authenticated Context → Agent Runtime → Tool
```

`employee_id`、`tenant_id`、role、access token 等可信身份信息应由 Runtime/Gateway 注入，不能让 LLM 自行生成。

## RAG

`app/rag/policy.py` 为零外部依赖的关键词检索实现。生产可保持 Tool 契约不变，替换为：

```text
Document → Parse → Chunk → Embedding → PostgreSQL + pgvector
→ Hybrid Retrieval → Rerank → Evidence → LLM Answer
```

## MCP Server

`app/mcp_server/server.py` 暴露：

- `get_leave_balance`
- `start_leave_request`
- `confirm_leave_request`
- `search_hr_policy`

MCP 不替代 Workflow 或企业 API；它提供 Agent 发现和调用这些能力的标准边界。

## 自动化测试

```bash
PYTHONPATH=. pytest -q
```

本次上传前实测：**6 passed**。覆盖 Tool 选择、Human Approval、余额不足、Workflow 完成、幂等、HTTP API、政策检索。

## Eval

```bash
PYTHONPATH=. python -m evals.runner
```

本次上传前示例 Golden Dataset 实测 5/5 Tool Selection 正确，`tool_selection_accuracy = 1.0`。这是小型确定性教学集，不代表生产模型效果；指标来自真实运行而非手写。

后续可扩展：Argument Accuracy、Task Completion、Trajectory Correctness、Unauthorized Action Rate、Hallucination Rate、Tool Calls、Latency、Cost。

## Build → Break → Fix → Eval

建议学习时主动破坏系统：

1. Build：跑通当前 Agent。
2. Break：删除余额校验，观察 E002 申请 3 天年假。
3. Fix：把确定性规则放回 Workflow。
4. Eval：用测试证明修复。
5. 再尝试删除 Human Approval、幂等、权限检查，观察测试如何暴露风险。

## 从 Demo 升级到生产

```text
SQLite → PostgreSQL
Keyword Retrieval → pgvector + Hybrid + Rerank
RuleBasedPlanner → LLM Model Adapter + Tool Calling
Demo employee_id → SSO/JWT Auth Context
单机 Workflow → Durable Workflow
基础 Trace → OpenTelemetry / Observability
示例 Eval → Golden Dataset + CI Release Gate
```

## 教学化简

当前版本有意简化：年假按自然日计算；Mock HR Backend 使用内存数据；RAG 为关键词检索；Planner 默认不调用收费模型；身份字段仅用于 Demo；不引入 Multi-Agent、LangChain/LangGraph/Temporal/Kubernetes。

## 验证说明

上传前已执行：

- `PYTHONPATH=. pytest -q` → **6 passed**
- `PYTHONPATH=. python -m evals.runner` → **5/5**
- Python 核心链路已实际验证。
- MCP Server 代码按 SDK v2 接口编写；当前测试环境未安装/启动 MCP CLI，因此 MCP 运行时启动仍需在安装依赖后单独验证。

## License

MIT。可用于学习、二次开发和课程演示。
