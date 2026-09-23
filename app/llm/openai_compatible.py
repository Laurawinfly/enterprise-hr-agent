"""OpenAI-compatible Chat Completions + Tool Calling adapter."""
import json
from app.llm.base import ModelTurn, ToolCall

class OpenAICompatibleProvider:
    def __init__(self, *, name, api_key, model, base_url=None, temperature=0, client=None):
        if not api_key and client is None:
            raise ValueError(f"{name} 未配置 API Key")
        if not model:
            raise ValueError(f"{name} 未配置模型名称")
        self.name, self.model, self.temperature = name, model, temperature
        self.api_key, self.base_url, self.client = api_key, base_url, client

    def complete(self, messages, tools):
        # Lazy creation keeps fake-client tests and rule mode independent of the optional SDK.
        if self.client is None:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, tools=tools,
            tool_choice="auto", temperature=self.temperature,
        )
        message = response.choices[0].message
        calls = []
        for call in message.tool_calls or []:
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError as exc:
                raise ValueError(f"{self.name} 返回非法 Tool JSON") from exc
            if not isinstance(args, dict):
                raise ValueError("Tool arguments 必须为 JSON object")
            calls.append(ToolCall(call.id, call.function.name, args))
        return ModelTurn(message.content, calls, message)

    def append_assistant_and_tool_results(self, messages, turn, tool_results):
        assistant = {"role": "assistant", "content": turn.content}
        if turn.tool_calls:
            assistant["tool_calls"] = [{
                "id": c.id, "type": "function",
                "function": {"name": c.name, "arguments": json.dumps(c.arguments, ensure_ascii=False)}
            } for c in turn.tool_calls]
        reasoning = getattr(turn.provider_message, "reasoning_content", None)
        if reasoning is not None:
            assistant["reasoning_content"] = reasoning
        messages.append(assistant)
        for call, result in tool_results:
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": json.dumps(result, ensure_ascii=False, default=str)})
