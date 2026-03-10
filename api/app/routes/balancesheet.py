
from app.models import get_balance_sheet, find_fund_by_id
from app.logger import get_logger

logger = get_logger("routes.balancesheet")


def _has_org_access(user, org_id):
    if user.get("isSuperAdmin"):
        return True
    return org_id in user.get("org_ids", [])


def get(fund_id, current_user):
    logger.info("Getting balance sheet for fund %s by user %s", fund_id, current_user["id"])
    try:
        fund = find_fund_by_id(fund_id)
        if not fund:
            logger.info("Fund not found: %s", fund_id)
            return 200, {"detail": "Fund not found", "noData": True}
        if not _has_org_access(current_user, fund["orgId"]):
            logger.info("Access denied: user %s not in org %s", current_user["id"], fund["orgId"])
            return 200, {"detail": "Not a member of this organization", "noData": True}

        result = get_balance_sheet(fund_id)
        if not result:
            logger.info("No balance sheet data for fund %s", fund_id)
            return 200, {"detail": "No balance sheet data found", "noData": True}

        logger.info("Balance sheet returned for fund %s", fund_id)
        return 200, result
    except Exception as e:
        logger.error("Failed to get balance sheet for fund %s: %s", fund_id, e, exc_info=True)
        return 200, {"detail": str(e), "noData": True}
