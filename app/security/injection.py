"""Heuristic input signal only; authorization and isolation remain the real controls."""
SUSPICIOUS = ["ignore previous instructions", "忽略之前", "system prompt", "developer message", "泄露密钥", "输出api key"]

def inspect_user_input(text):
    hits = [x for x in SUSPICIOUS if x.lower() in text.lower()]
    return {"suspicious": bool(hits), "signals": hits}
