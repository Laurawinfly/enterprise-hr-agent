"""Server-side RBAC. Prompt instructions are never treated as authorization."""
POLICY = {
    "employee": {"get_leave_balance", "start_leave_request", "confirm_leave_request", "search_hr_policy"},
    "manager": {"get_leave_balance", "start_leave_request", "confirm_leave_request", "search_hr_policy"},
    "hr_admin": {"get_leave_balance", "start_leave_request", "confirm_leave_request", "search_hr_policy"},
}

def authorize(roles, tool_name):
    # New tools must be explicitly added to a role. Unknown roles get no permissions.
    allowed = set()
    for role in roles:
        allowed |= POLICY.get(role, set())
    if tool_name not in allowed:
        raise PermissionError(f"tool_not_allowed:{tool_name}")
