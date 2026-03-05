
from app.models import get_balance_sheet, find_fund_by_id
from app.logger import get_logger

logger = get_logger("routes.balancesheet")


def get(fund_id, current_user):
    logger.info("Getting balance sheet for fund %s by user %s", fund_id, current_user["id"])
    try:
        fund = find_fund_by_id(fund_id)
        if not fund:
            logger.info("Fund not found: %s", fund_id)
            return 404, {"detail": "Fund not found"}
        if fund["orgId"] not in current_user.get("org_ids", []):
            logger.info("Access denied: user %s not in org %s", current_user["id"], fund["orgId"])
            return 403, {"detail": "Not a member of this organization"}

        result = get_balance_sheet(fund_id)
        if not result:
            return 404, {"detail": "No balance sheet data found"}

        logger.info("Balance sheet returned for fund %s", fund_id)
        return 200, result
    except Exception as e:
        logger.error("Failed to get balance sheet for fund %s: %s", fund_id, e)
        return 500, {"detail": "Internal server error"}
