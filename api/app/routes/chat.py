"""
Chat route – answers portfolio questions using real org data.
Pattern-matches user questions to data queries and formats responses.
"""
import re
from app.models import (
    list_funds_by_org, list_properties_by_org,
    get_org_members, get_noi_vs_budget_by_org,
)
from app.models.balancesheet import get_balance_sheet
from app.database import (
    funds_col, properties_col, tenants_col, units_col,
    sqft_col, fund_properties_col, fund_transactions_col,
)
from app.logger import get_logger

logger = get_logger("routes.chat")


def _fmt(value):
    """Format number as currency string."""
    if value is None:
        return "$0"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def _pct(value):
    if value is None:
        return "0.00%"
    return f"{value * 100:.2f}%" if abs(value) < 100 else f"{value:.2f}%"


def _get_fund_summaries(org_id):
    """Get balance sheet summary for all funds in an org."""
    funds = list_funds_by_org(org_id)
    summaries = []
    for f in funds:
        bs = get_balance_sheet(f["id"])
        if bs:
            summaries.append(bs)
    return funds, summaries


def _portfolio_summary(org_id):
    """High-level portfolio summary."""
    funds, summaries = _get_fund_summaries(org_id)
    props = list_properties_by_org(org_id)
    members = get_org_members(org_id)

    total_aum = sum(s.get("aum", 0) or 0 for s in summaries)
    total_noi = sum(s.get("noi", 0) or 0 for s in summaries)
    total_revenue = sum(s.get("revenue", 0) or 0 for s in summaries)

    return (
        f"**Portfolio Summary**\n\n"
        f"- **Funds:** {len(funds)}\n"
        f"- **Properties:** {len(props)}\n"
        f"- **Members:** {len(members)}\n"
        f"- **Total AUM:** {_fmt(total_aum)}\n"
        f"- **Total NOI:** {_fmt(total_noi)}\n"
        f"- **Total Revenue:** {_fmt(total_revenue)}\n\n"
        f"*Source: Balance sheet aggregation across {len(summaries)} funds with data.*"
    )


def _noi_budget(org_id):
    """NOI vs budget comparison."""
    noi_data = get_noi_vs_budget_by_org(org_id)
    if not noi_data:
        return "No NOI vs budget data available for this organization."

    total_actual = sum(v.get("noiActual", 0) for v in noi_data.values())
    total_budget = sum(v.get("noiBudget", 0) for v in noi_data.values())
    variance = total_actual - total_budget
    variance_pct = (variance / total_budget * 100) if total_budget else 0

    # Top 5 variances
    sorted_props = sorted(
        noi_data.items(),
        key=lambda x: abs(x[1].get("noiVariance", 0)),
        reverse=True,
    )[:5]

    lines = [
        f"**Portfolio NOI vs Budget**\n",
        f"- **Actual NOI:** {_fmt(total_actual)}",
        f"- **Budget NOI:** {_fmt(total_budget)}",
        f"- **Variance:** {_fmt(variance)} ({variance_pct:+.1f}%)\n",
        f"**Top 5 Variance Drivers:**\n",
    ]
    for code, v in sorted_props:
        var = v.get("noiVariance", 0)
        lines.append(f"- {code}: {_fmt(var)} variance (Actual: {_fmt(v.get('noiActual', 0))}, Budget: {_fmt(v.get('noiBudget', 0))})")

    lines.append(f"\n*Source: GL totals aggregation, {len(noi_data)} properties.*")
    return "\n".join(lines)


def _fund_performance(org_id):
    """Fund-level performance including returns."""
    funds, summaries = _get_fund_summaries(org_id)
    if not summaries:
        return "No fund performance data available."

    lines = ["**Fund Performance Summary**\n"]
    for s in summaries:
        if s.get("noData"):
            continue
        name = s.get("fundName", s.get("fundCode", "Unknown"))
        lines.append(f"**{name}** ({s.get('fundCode', '')})")
        lines.append(f"  - AUM: {_fmt(s.get('aum', 0))}")
        lines.append(f"  - NOI: {_fmt(s.get('noi', 0))}")
        lines.append(f"  - Revenue: {_fmt(s.get('revenue', 0))}")
        lines.append(f"  - Cash: {_fmt(s.get('cash', 0))}")
        dscr = s.get("dscr", 0) or 0
        lines.append(f"  - DSCR: {dscr:.2f}x")
        ytd = s.get("ytdReturn", 0) or 0
        lines.append(f"  - YTD Return: {_pct(ytd)}")
        lines.append("")

    lines.append(f"*Source: Balance sheet data for {len([s for s in summaries if not s.get('noData')])} funds.*")
    return "\n".join(lines)


def _dscr_query(org_id, question):
    """DSCR for a specific property or fund."""
    funds, summaries = _get_fund_summaries(org_id)
    q_lower = question.lower()

    # Try to match a fund name
    for s in summaries:
        fund_name = (s.get("fundName") or "").lower()
        fund_code = (s.get("fundCode") or "").lower()
        if fund_name and fund_name in q_lower or fund_code and fund_code in q_lower:
            dscr = s.get("dscr", 0) or 0
            noi = s.get("noi", 0) or 0
            return (
                f"**DSCR for {s.get('fundName')}**\n\n"
                f"- **DSCR:** {dscr:.2f}x\n"
                f"- **NOI:** {_fmt(noi)}\n\n"
                f"*Source: Balance sheet calculation for fund {s.get('fundCode')}.*"
            )

    # Return all fund DSCRs
    lines = ["**Portfolio DSCR by Fund**\n"]
    for s in summaries:
        if s.get("noData"):
            continue
        dscr = s.get("dscr", 0) or 0
        lines.append(f"- **{s.get('fundName', 'Unknown')}:** {dscr:.2f}x")
    lines.append(f"\n*Source: Balance sheet data.*")
    return "\n".join(lines)


def _expense_variance(org_id):
    """Top expense variance drivers."""
    noi_data = get_noi_vs_budget_by_org(org_id)
    if not noi_data:
        return "No expense variance data available."

    sorted_props = sorted(
        noi_data.items(),
        key=lambda x: abs(x[1].get("noiVariance", 0)),
        reverse=True,
    )[:5]

    lines = ["**Top Expense Variance Drivers**\n"]
    for i, (code, v) in enumerate(sorted_props, 1):
        var = v.get("noiVariance", 0)
        direction = "over" if var < 0 else "under"
        lines.append(f"{i}. **{code}:** {_fmt(abs(var))} {direction} budget")
        lines.append(f"   - Actual: {_fmt(v.get('noiActual', 0))}, Budget: {_fmt(v.get('noiBudget', 0))}")

    lines.append(f"\n*Source: GL totals aggregation.*")
    return "\n".join(lines)


def _property_overview(org_id):
    """Property portfolio overview."""
    props = list_properties_by_org(org_id)
    if not props:
        return "No properties found for this organization."

    by_type = {}
    by_market = {}
    by_status = {}
    for p in props:
        pt = p.get("propertyType", "unknown")
        by_type[pt] = by_type.get(pt, 0) + 1
        mkt = p.get("market", "unknown")
        by_market[mkt] = by_market.get(mkt, 0) + 1
        st = p.get("status", "unknown")
        by_status[st] = by_status.get(st, 0) + 1

    lines = [f"**Property Portfolio Overview** ({len(props)} properties)\n"]

    lines.append("**By Type:**")
    for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
        lines.append(f"  - {t.title()}: {c}")

    lines.append("\n**By Market (Top 10):**")
    for m, c in sorted(by_market.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"  - {m}: {c}")

    lines.append("\n**By Status:**")
    for s, c in sorted(by_status.items(), key=lambda x: -x[1]):
        lines.append(f"  - {s.title()}: {c}")

    lines.append(f"\n*Source: Properties collection.*")
    return "\n".join(lines)


def _tenant_overview(org_id):
    """Tenant / lease overview."""
    props = list_properties_by_org(org_id)
    prop_ids = [p["id"] for p in props]
    if not prop_ids:
        return "No tenant data available."

    tenant_count = tenants_col.count_documents({"propertyId": {"$in": prop_ids}})
    unit_count = units_col.count_documents({"propertyId": {"$in": prop_ids}})

    lines = [
        f"**Tenant & Lease Overview**\n",
        f"- **Total Tenants:** {tenant_count:,}",
        f"- **Total Units:** {unit_count:,}",
        f"- **Properties:** {len(props)}",
        f"- **Occupancy proxy:** {tenant_count}/{unit_count} units leased" if unit_count else "",
        f"\n*Source: Tenants and units collections.*",
    ]
    return "\n".join(lines)


def _fund_list(org_id):
    """List all funds."""
    funds = list_funds_by_org(org_id)
    if not funds:
        return "No funds found for this organization."

    lines = [f"**Funds** ({len(funds)} total)\n"]
    for f in funds[:20]:
        lines.append(f"- **{f.get('fundName', '')}** ({f.get('fundCode', '')}) – {f.get('fundType', '')} – {f.get('baseCurrency', '')} – Status: {f.get('status', '')}")

    if len(funds) > 20:
        lines.append(f"\n*...and {len(funds) - 20} more funds.*")
    lines.append(f"\n*Source: Funds collection.*")
    return "\n".join(lines)


def _members_overview(org_id):
    """List members/users of the org."""
    members = get_org_members(org_id)
    if not members:
        return "No members found for this organization."

    lines = [f"**Organization Members** ({len(members)} total)\n"]
    for m in members[:20]:
        name = f"{m.get('firstName', '')} {m.get('lastName', '')}".strip() or m.get('email', 'Unknown')
        roles = ", ".join(m.get("roles", [])) if m.get("roles") else "N/A"
        lines.append(f"- **{name}** – {m.get('email', '')} – Roles: {roles}")
    if len(members) > 20:
        lines.append(f"\n*...and {len(members) - 20} more members.*")
    lines.append(f"\n*Source: Organization members.*")
    return "\n".join(lines)


# Stop words to exclude from flexible search
STOP_WORDS = {
    "the", "this", "that", "what", "which", "who", "how", "when", "where",
    "are", "was", "were", "been", "being", "have", "has", "had", "having",
    "does", "did", "doing", "will", "would", "could", "should", "may",
    "can", "for", "and", "but", "not", "you", "all", "any", "our", "your",
    "its", "his", "her", "they", "them", "from", "with", "about", "into",
    "show", "give", "get", "list", "tell", "please", "org", "organization",
    "data", "info", "information", "me", "my",
}


def _safe_str(val):
    """Safely convert a value to lowercase string."""
    if val is None:
        return ""
    if isinstance(val, str):
        return val.lower()
    return str(val).lower()


def _flexible_search(org_id, question):
    """Search across all collections for any matching data based on the user's question."""
    q_lower = question.lower()
    words = [w for w in re.findall(r'[a-z]+', q_lower) if w not in STOP_WORDS and len(w) > 2]
    sections = []

    # --- Search funds ---
    funds = list_funds_by_org(org_id)
    matched_funds = []
    for f in funds:
        name = _safe_str(f.get("fundName"))
        code = _safe_str(f.get("fundCode"))
        ftype = _safe_str(f.get("fundType"))
        if any(w in name or w in code or w in ftype for w in words):
            matched_funds.append(f)

    if matched_funds:
        lines = [f"**Matching Funds** ({len(matched_funds)} found)\n"]
        for f in matched_funds[:15]:
            lines.append(f"- **{f.get('fundName', '')}** ({f.get('fundCode', '')}) – {f.get('fundType', '')} – {f.get('baseCurrency', '')} – Status: {f.get('status', '')}")
        sections.append("\n".join(lines))

    # --- Search properties ---
    props = list_properties_by_org(org_id)
    matched_props = []
    for p in props:
        searchable = " ".join([
            _safe_str(p.get("propertyName")),
            _safe_str(p.get("propertyCode")),
            _safe_str(p.get("market")),
            _safe_str(p.get("propertyType")),
            _safe_str(p.get("address")),
            _safe_str(p.get("city")),
            _safe_str(p.get("state")),
        ])
        if words and any(w in searchable for w in words):
            matched_props.append(p)

    if matched_props:
        lines = [f"**Matching Properties** ({len(matched_props)} found)\n"]
        for p in matched_props[:15]:
            lines.append(
                f"- **{p.get('propertyName', p.get('propertyCode', ''))}** "
                f"({p.get('propertyCode', '')}) – {p.get('propertyType', '')} – "
                f"{p.get('market', '')} – {p.get('city', '')}, {p.get('state', '')} – "
                f"Status: {p.get('status', '')}"
            )
        if len(matched_props) > 15:
            lines.append(f"\n*...and {len(matched_props) - 15} more.*")
        sections.append("\n".join(lines))

    # --- Search tenants ---
    prop_ids = [p["id"] for p in props]
    if prop_ids:
        tenant_query = {"propertyId": {"$in": prop_ids}}
        # Build text search filter from keywords
        or_filters = []
        for w in words:
            rgx = {"$regex": w, "$options": "i"}
            or_filters.append({"tenantName": rgx})
            or_filters.append({"company": rgx})
            or_filters.append({"unitNumber": rgx})
        if or_filters:
            tenant_query["$or"] = or_filters
            matched_tenants = list(tenants_col.find(tenant_query).limit(15))
            if matched_tenants:
                lines = [f"**Matching Tenants** ({len(matched_tenants)} found)\n"]
                for t in matched_tenants:
                    tname = t.get("tenantName") or t.get("company") or "Unknown"
                    lines.append(
                        f"- **{tname}** – Unit: {t.get('unitNumber', 'N/A')} – "
                        f"Property: {t.get('propertyId', '')}"
                    )
                sections.append("\n".join(lines))

    # --- If no specific matches, return everything we have ---
    if not sections:
        # Give a comprehensive overview
        lines = [f"**Organization Data Overview**\n"]
        lines.append(f"- **Funds:** {len(funds)}")
        lines.append(f"- **Properties:** {len(props)}")

        if prop_ids:
            tenant_count = tenants_col.count_documents({"propertyId": {"$in": prop_ids}})
            unit_count = units_col.count_documents({"propertyId": {"$in": prop_ids}})
            lines.append(f"- **Tenants:** {tenant_count:,}")
            lines.append(f"- **Units:** {unit_count:,}")

        txn_count = fund_transactions_col.count_documents({"fundId": {"$in": [f["id"] for f in funds]}}) if funds else 0
        if txn_count:
            lines.append(f"- **Transactions:** {txn_count:,}")

        lines.append(f"\n**Funds:**")
        for f in funds[:10]:
            lines.append(f"- {f.get('fundName', '')} ({f.get('fundCode', '')})")
        if len(funds) > 10:
            lines.append(f"  *...and {len(funds) - 10} more*")

        lines.append(f"\n**Properties (first 10):**")
        for p in props[:10]:
            lines.append(f"- {p.get('propertyName', p.get('propertyCode', ''))} – {p.get('propertyType', '')} – {p.get('market', '')}")
        if len(props) > 10:
            lines.append(f"  *...and {len(props) - 10} more*")

        lines.append(f"\n*Try asking about specific fund names, property types, markets, or metrics like NOI, DSCR, AUM.*")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


# ---- Question routing ----

PATTERNS = [
    (r"(portfolio|overall)\s*(summary|overview|status)", "summary"),
    (r"(noi|net operating income).*(budget|compare|vs|variance)", "noi_budget"),
    (r"(budget|actual).*(noi|variance|compare)", "noi_budget"),
    (r"fund\s*performance|performance.*fund|return.*fund|fund.*return", "fund_performance"),
    (r"summarize.*fund|fund.*summary", "fund_performance"),
    (r"dscr|debt\s*service\s*coverage", "dscr"),
    (r"expense\s*variance|variance\s*driver|top.*expense", "expense_variance"),
    (r"(property|properties|asset|assets).*(overview|summary|list|breakdown|type|market)", "properties"),
    (r"(list|show|all).*(property|properties|asset|assets)", "properties"),
    (r"(member|members|user|users|team|people)", "members"),
    (r"(tenant|lease|occupancy|unit)", "tenants"),
    (r"(list|show|all)\s*(fund|funds)", "fund_list"),
    (r"(aum|assets\s*under\s*management)", "summary"),
    (r"(eum|equity\s*under\s*management)", "summary"),
    (r"(cash|liquidity)", "fund_performance"),
    (r"(revenue|income)", "fund_performance"),
    (r"how\s*many\s*(fund|propert|member|tenant|unit)", "summary"),
]


def handle_chat(org_id, body, current_user):
    """Process a chat message and return a data-driven response."""
    logger.info("Chat query for org %s by user %s", org_id, current_user["id"])

    if not current_user.get("isSuperAdmin") and org_id not in current_user.get("org_ids", []):
        return 403, {"detail": "Not a member of this organization"}

    question = body.get("message", "").strip()
    if not question:
        return 400, {"detail": "message is required"}

    q_lower = question.lower()

    # Match question to handler
    handler_key = None
    for pattern, key in PATTERNS:
        if re.search(pattern, q_lower):
            handler_key = key
            break

    try:
        if handler_key == "summary":
            response = _portfolio_summary(org_id)
        elif handler_key == "noi_budget":
            response = _noi_budget(org_id)
        elif handler_key == "fund_performance":
            response = _fund_performance(org_id)
        elif handler_key == "dscr":
            response = _dscr_query(org_id, question)
        elif handler_key == "expense_variance":
            response = _expense_variance(org_id)
        elif handler_key == "properties":
            response = _property_overview(org_id)
        elif handler_key == "tenants":
            response = _tenant_overview(org_id)
        elif handler_key == "fund_list":
            response = _fund_list(org_id)
        elif handler_key == "members":
            response = _members_overview(org_id)
        else:
            # No pattern matched – do flexible search across all collections
            response = _flexible_search(org_id, question)

        logger.info("Chat response generated for org %s, handler=%s", org_id, handler_key or "help")
        return 200, {"response": response, "query_type": handler_key or "help"}

    except Exception as e:
        logger.error("Chat query failed for org %s: %s", org_id, e)
        return 500, {"detail": "Failed to process query"}
