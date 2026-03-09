from app.models import (
    create_fund, find_fund_by_id, list_funds_by_org, update_fund, delete_fund
)
from app.logger import get_logger

logger = get_logger("routes.funds")


def list_funds(org_id, current_user):
    logger.info("Listing funds for org %s by user %s", org_id, current_user["id"])
    if org_id not in current_user.get("org_ids", []):
        logger.info("Access denied: user %s not in org %s", current_user["id"], org_id)
        return 403, {"detail": "Not a member of this organization"}
    try:
        funds = list_funds_by_org(org_id)
        logger.info("Found %d funds for org %s", len(funds), org_id)
        return 200, funds
    except Exception as e:
        logger.error("Failed to list funds for org %s: %s", org_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def get_fund(fund_id, current_user):
    logger.info("Getting fund %s by user %s", fund_id, current_user["id"])
    try:
        fund = find_fund_by_id(fund_id)
        if not fund:
            logger.info("Fund not found: %s", fund_id)
            return 404, {"detail": "Fund not found"}
        if fund["orgId"] not in current_user.get("org_ids", []):
            logger.info("Access denied: user %s not in org %s", current_user["id"], fund["orgId"])
            return 403, {"detail": "Not a member of this organization"}
        logger.info("Fund fetched: %s", fund_id)
        return 200, fund
    except Exception as e:
        logger.error("Failed to get fund %s: %s", fund_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}

def create(org_id, body, current_user):
    logger.info("Creating fund in org %s by user %s", org_id, current_user["id"])
    if org_id not in current_user.get("org_ids", []):
        logger.info("Access denied: user %s not in org %s", current_user["id"], org_id)
        return 403, {"detail": "Not a member of this organization"}

    fund_code = body.get("fundCode")
    fund_name = body.get("fundName")
    if not fund_code or not fund_name:
        logger.info("Create fund failed: missing fundCode or fundName")
        return 400, {"detail": "fundCode and fundName are required"}

    try:
        fund_id = create_fund(org_id, body)
        logger.info("Fund created: id=%s in org %s", fund_id, org_id)
        return 201, {"id": fund_id}
    except Exception as e:
        logger.error("Failed to create fund in org %s: %s", org_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def update(fund_id, body, current_user):
    logger.info("Updating fund %s by user %s", fund_id, current_user["id"])
    try:
        fund = find_fund_by_id(fund_id)
        if not fund:
            logger.info("Fund not found: %s", fund_id)
            return 404, {"detail": "Fund not found"}
        if fund["orgId"] not in current_user.get("org_ids", []):
            logger.info("Access denied: user %s not in org %s", current_user["id"], fund["orgId"])
            return 403, {"detail": "Not a member of this organization"}
        update_fund(fund_id, body)
        logger.info("Fund %s updated", fund_id)
        return 200, {"detail": "Fund updated"}
    except Exception as e:
        logger.error("Failed to update fund %s: %s", fund_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def delete(fund_id, current_user):
    logger.info("Deleting fund %s by user %s", fund_id, current_user["id"])
    try:
        fund = find_fund_by_id(fund_id)
        if not fund:
            logger.info("Fund not found: %s", fund_id)
            return 404, {"detail": "Fund not found"}
        if fund["orgId"] not in current_user.get("org_ids", []):
            logger.info("Access denied: user %s not in org %s", current_user["id"], fund["orgId"])
            return 403, {"detail": "Not a member of this organization"}
        delete_fund(fund_id)
        logger.info("Fund %s deleted", fund_id)
        return 200, {"detail": "Fund deleted"}
    except Exception as e:
        logger.error("Failed to delete fund %s: %s", fund_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}
