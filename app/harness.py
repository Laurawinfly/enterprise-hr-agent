"""Deterministic governance layer around model-directed tool execution."""
from dataclasses import dataclass
from app.security.permissions import authorize
from app.security.injection import inspect_user_input
from app.security.redaction import redact
from app.governance.audit import audit
from app.governance.resilience import with_timeout_retry

@dataclass
class Harness:
    tool_timeout_s: float = 8
    tool_retries: int = 1

    def inspect_input(self, text):
        result = inspect_user_input(text)
        audit("input_inspected", result=result)
        return result

    def authorize_tool(self, auth, tool):
        authorize(auth.roles, tool)
        audit("tool_authorized", employee_id=auth.employee_id, tenant_id=auth.tenant_id, tool=tool)

    async def execute_tool(self, transport, auth, name, args):
        # The model proposes a tool call; the harness makes the authorization decision.
        self.authorize_tool(auth, name)
        audit("tool_started", employee_id=auth.employee_id, tenant_id=auth.tenant_id, tool=name, args=args)
        try:
            result = await with_timeout_retry(
                lambda: transport.call(name, args, auth.employee_id),
                timeout_s=self.tool_timeout_s,
                retries=self.tool_retries,
            )
            audit("tool_succeeded", tool=name, result=result)
            return result
        except Exception as exc:
            audit("tool_failed", tool=name, error=str(exc))
            raise

    def safe_trace(self, trace):
        return redact(trace)
