"""Weekly Report Service for the MPCP Project Tracker.

Handles:
- HTML email template generation
- Microsoft Graph API sendMail integration
- Recipient config management

Requirements: 17, 18, 19, 22
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from app.models.mpcp_schemas import (
    CheckPoint,
    Dependency,
    DependencyStatus,
    ExecutionMilestone,
    ManagingPoint,
    Project,
    RAGStatus,
    WeeklyReportConfig,
)

logger = logging.getLogger(__name__)

# Default config stored in memory (persisted via admin endpoint)
_report_config = WeeklyReportConfig(
    to=["suraj.ray@tvsmotor.com"],
    cc=[],
    include_all_bus=True,
)


def get_report_config() -> WeeklyReportConfig:
    return _report_config


def update_report_config(config: WeeklyReportConfig) -> WeeklyReportConfig:
    global _report_config
    _report_config = config
    return _report_config


def generate_weekly_report_html(
    projects: List[Project],
    milestones: Dict[str, List[ExecutionMilestone]],
    dependencies: Dict[str, List[Dependency]],
    mps: List[ManagingPoint],
    cps: List[CheckPoint],
) -> str:
    """Generate HTML email body for the weekly report."""
    red_projects = [p for p in projects if p.rag_status == RAGStatus.RED]
    yellow_projects = [p for p in projects if p.rag_status == RAGStatus.YELLOW]
    green_count = sum(1 for p in projects if p.rag_status == RAGStatus.GREEN)

    # Top 5 slippages
    all_milestones = []
    for pid, ms_list in milestones.items():
        proj = next((p for p in projects if p.id == pid), None)
        for m in ms_list:
            if m.slippage_days and m.slippage_days > 0:
                all_milestones.append((proj, m))
    all_milestones.sort(key=lambda x: x[1].slippage_days or 0, reverse=True)
    top_slippages = all_milestones[:5]

    # Overdue/escalated dependencies
    overdue_deps = []
    for pid, deps in dependencies.items():
        proj = next((p for p in projects if p.id == pid), None)
        for d in deps:
            if d.status in (DependencyStatus.ESCALATED,) or (d.is_overdue and d.status != DependencyStatus.RESOLVED):
                overdue_deps.append((proj, d))
    overdue_deps.sort(key=lambda x: x[1].cutoff_date)

    # Domain breakdown
    domain_counts: Dict[str, Dict[str, int]] = {}
    for p in projects:
        dom = p.domain.value if p.domain else "Untagged"
        if dom not in domain_counts:
            domain_counts[dom] = {"total": 0, "Green": 0, "Yellow": 0, "Red": 0}
        domain_counts[dom]["total"] += 1
        domain_counts[dom][p.rag_status.value] += 1

    # Build HTML
    html = f"""
    <html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#333;max-width:700px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#1a237e,#3949ab);color:white;padding:20px 24px;border-radius:8px 8px 0 0;">
        <h2 style="margin:0;">📈 TVS PlanIQ — MPCP Weekly Report</h2>
        <p style="margin:4px 0 0;opacity:0.8;font-size:13px;">{date.today().strftime('%B %d, %Y')}</p>
    </div>
    <div style="padding:20px 24px;background:#fff;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 8px 8px;">
    """

    # RAG Summary
    html += f"""
    <h3 style="color:#1a237e;border-bottom:2px solid #e8eaf6;padding-bottom:8px;">Portfolio Health</h3>
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
        <tr><td style="padding:8px;background:#e8f5e9;text-align:center;border-radius:6px;"><strong style="font-size:20px;color:#2e7d32;">{green_count}</strong><br><small>Green</small></td>
        <td style="padding:8px;background:#fff8e1;text-align:center;border-radius:6px;"><strong style="font-size:20px;color:#f57f17;">{len(yellow_projects)}</strong><br><small>Yellow</small></td>
        <td style="padding:8px;background:#ffebee;text-align:center;border-radius:6px;"><strong style="font-size:20px;color:#c62828;">{len(red_projects)}</strong><br><small>Red</small></td>
        <td style="padding:8px;background:#e3f2fd;text-align:center;border-radius:6px;"><strong style="font-size:20px;color:#1565c0;">{len(projects)}</strong><br><small>Total</small></td></tr>
    </table>
    """

    if not red_projects and not yellow_projects:
        html += '<p style="color:#2e7d32;font-weight:600;font-size:16px;">✅ All projects on track!</p>'
    else:
        # Red items
        if red_projects:
            html += '<h3 style="color:#c62828;">🔴 Red Items</h3><table style="width:100%;border-collapse:collapse;font-size:12px;">'
            html += '<tr style="background:#f5f5f5;"><th style="padding:6px;text-align:left;">Project</th><th>Why</th><th>Owner</th><th>ETA</th></tr>'
            for p in red_projects:
                ctx = p.rag_context
                html += f'<tr><td style="padding:6px;border-bottom:1px solid #eee;">{p.name}</td><td>{ctx.why if ctx else "-"}</td><td>{ctx.who if ctx else "-"}</td><td>{ctx.eta if ctx else "-"}</td></tr>'
            html += '</table><br>'

        # Yellow items
        if yellow_projects:
            html += '<h3 style="color:#f57f17;">🟡 Yellow Items</h3><table style="width:100%;border-collapse:collapse;font-size:12px;">'
            html += '<tr style="background:#f5f5f5;"><th style="padding:6px;text-align:left;">Project</th><th>Why</th><th>Owner</th><th>ETA</th></tr>'
            for p in yellow_projects:
                ctx = p.rag_context
                html += f'<tr><td style="padding:6px;border-bottom:1px solid #eee;">{p.name}</td><td>{ctx.why if ctx else "-"}</td><td>{ctx.who if ctx else "-"}</td><td>{ctx.eta if ctx else "-"}</td></tr>'
            html += '</table><br>'

    # Top slippages
    if top_slippages:
        html += '<h3 style="color:#1a237e;">📊 Top 5 Milestone Slippages</h3><table style="width:100%;border-collapse:collapse;font-size:12px;">'
        html += '<tr style="background:#f5f5f5;"><th style="padding:6px;text-align:left;">Project</th><th>Milestone</th><th>Slippage</th></tr>'
        for proj, m in top_slippages:
            html += f'<tr><td style="padding:6px;border-bottom:1px solid #eee;">{proj.name if proj else "?"}</td><td>{m.name}</td><td style="color:#c62828;font-weight:600;">+{m.slippage_days}d</td></tr>'
        html += '</table><br>'

    # Overdue dependencies
    if overdue_deps:
        html += '<h3 style="color:#e65100;">⚠️ Overdue/Escalated Dependencies</h3><table style="width:100%;border-collapse:collapse;font-size:12px;">'
        html += '<tr style="background:#f5f5f5;"><th style="padding:6px;text-align:left;">Project</th><th>Dependency</th><th>Owner</th><th>Cutoff</th></tr>'
        for proj, d in overdue_deps[:10]:
            html += f'<tr><td style="padding:6px;border-bottom:1px solid #eee;">{proj.name if proj else "?"}</td><td>{d.description}</td><td>{d.external_owner}</td><td style="color:#c62828;">{d.cutoff_date}</td></tr>'
        html += '</table><br>'

    # Domain breakdown
    if domain_counts:
        html += '<h3 style="color:#1a237e;">🏷️ By Domain</h3><table style="width:100%;border-collapse:collapse;font-size:12px;">'
        html += '<tr style="background:#f5f5f5;"><th style="padding:6px;text-align:left;">Domain</th><th>Total</th><th>Green</th><th>Yellow</th><th>Red</th></tr>'
        for dom, c in domain_counts.items():
            html += f'<tr><td style="padding:6px;border-bottom:1px solid #eee;">{dom}</td><td>{c["total"]}</td><td style="color:#2e7d32;">{c["Green"]}</td><td style="color:#f57f17;">{c["Yellow"]}</td><td style="color:#c62828;">{c["Red"]}</td></tr>'
        html += '</table><br>'

    # Footer
    html += """
    <hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0;">
    <p style="font-size:12px;color:#666;">
        <a href="http://localhost:8000/#mpcp-tracker" style="color:#1a237e;text-decoration:none;font-weight:600;">Open TVS PlanIQ MPCP Tracker →</a><br>
        This report was auto-generated by TVS PlanIQ.
    </p>
    </div></body></html>
    """
    return html


async def send_report_email(
    html_body: str,
    config: WeeklyReportConfig,
    sp,
) -> bool:
    """Send the weekly report via Microsoft Graph API sendMail.

    Uses the same service account credentials as SharePoint.
    """
    import httpx

    try:
        await sp._ensure_authenticated()
        headers = sp._get_headers()
        headers["Content-Type"] = "application/json"

        # Build email payload
        message = {
            "message": {
                "subject": f"TVS PlanIQ — MPCP Weekly Report ({date.today().strftime('%d %b %Y')})",
                "body": {"contentType": "HTML", "content": html_body},
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in config.to],
                "ccRecipients": [{"emailAddress": {"address": addr}} for addr in config.cc],
            },
            "saveToSentItems": "true",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://graph.microsoft.com/v1.0/me/sendMail",
                headers=headers,
                json=message,
            )
            if resp.status_code == 202:
                logger.info("Weekly report email sent successfully")
                return True
            else:
                logger.error(f"Failed to send email: {resp.status_code} {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False
