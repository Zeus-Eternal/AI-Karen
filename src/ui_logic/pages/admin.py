"""
Kari Admin Page
- Orchestrates: diagnostics, org admin, audit log, RBAC, system status
- Only layout and context passing
"""

from components.admin.diagnostics import render_diagnostics
from components.admin.org_admin import render_org_admin
from components.admin.audit_log import render_audit_log
from components.admin.rbac_panel import render_rbac_panel
from components.admin.system_status import render_system_status

def admin_page(user_ctx=None):
    # Top: System Status + Diagnostics
    render_system_status(user_ctx=user_ctx)
    render_diagnostics(user_ctx=user_ctx)
    # Middle: Org Admin + RBAC controls
    render_org_admin(user_ctx=user_ctx)
    render_rbac_panel(user_ctx=user_ctx)
    # Bottom: Audit logs
    render_audit_log(user_ctx=user_ctx)
