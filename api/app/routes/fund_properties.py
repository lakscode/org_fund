from app.models import (
    create_fund_property, find_fund_property_by_id,
    list_fund_properties_by_fund, list_fund_properties_by_property,
    list_fund_properties_by_org, update_fund_property, delete_fund_property,
)
from app.logger import get_logger

logger = get_logger("routes.fund_properties")


def _has_org_access(user, org_id):
    if user.get("isSuperAdmin"):
        return True
    return org_id in user.get("org_ids", [])


def list_by_org(org_id, current_user):
    logger.info("Listing fund-properties for org %s by user %s", org_id, current_user["id"])
    if not _has_org_access(current_user, org_id):
        logger.info("Access denied: user %s not in org %s", current_user["id"], org_id)
        return 403, {"detail": "Not a member of this organization"}
    try:
        fps = list_fund_properties_by_org(org_id)
        logger.info("Found %d fund-property links for org %s", len(fps), org_id)
        return 200, fps
    except Exception as e:
        logger.error("Failed to list fund-properties for org %s: %s", org_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def list_by_fund(fund_id, current_user):
    logger.info("Listing fund-properties for fund %s by user %s", fund_id, current_user["id"])
    try:
        fps = list_fund_properties_by_fund(fund_id)
        logger.info("Found %d fund-property links for fund %s", len(fps), fund_id)
        return 200, fps
    except Exception as e:
        logger.error("Failed to list fund-properties for fund %s: %s", fund_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def list_by_property(property_id, current_user):
    logger.info("Listing fund-properties for property %s by user %s", property_id, current_user["id"])
    try:
        fps = list_fund_properties_by_property(property_id)
        logger.info("Found %d fund-property links for property %s", len(fps), property_id)
        return 200, fps
    except Exception as e:
        logger.error("Failed to list fund-properties for property %s: %s", property_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def get(fp_id, current_user):
    logger.info("Getting fund-property %s by user %s", fp_id, current_user["id"])
    try:
        fp = find_fund_property_by_id(fp_id)
        if not fp:
            logger.info("Fund-property not found: %s", fp_id)
            return 404, {"detail": "Fund-property not found"}
        if not _has_org_access(current_user, fp["orgId"]):
            logger.info("Access denied: user %s not in org %s", current_user["id"], fp["orgId"])
            return 403, {"detail": "Not a member of this organization"}
        logger.info("Fund-property fetched: %s", fp_id)
        return 200, fp
    except Exception as e:
        logger.error("Failed to get fund-property %s: %s", fp_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def create(org_id, body, current_user):
    logger.info("Creating fund-property in org %s by user %s", org_id, current_user["id"])
    if not _has_org_access(current_user, org_id):
        logger.info("Access denied: user %s not in org %s", current_user["id"], org_id)
        return 403, {"detail": "Not a member of this organization"}

    fund_id = body.get("fundId")
    property_id = body.get("propertyId")
    if not fund_id or not property_id:
        logger.info("Create fund-property failed: missing fundId or propertyId")
        return 400, {"detail": "fundId and propertyId are required"}

    try:
        fp_id = create_fund_property(org_id, body)
        logger.info("Fund-property created: id=%s in org %s", fp_id, org_id)
        return 201, {"id": fp_id}
    except Exception as e:
        logger.error("Failed to create fund-property in org %s: %s", org_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def update(fp_id, body, current_user):
    logger.info("Updating fund-property %s by user %s", fp_id, current_user["id"])
    try:
        fp = find_fund_property_by_id(fp_id)
        if not fp:
            logger.info("Fund-property not found: %s", fp_id)
            return 404, {"detail": "Fund-property not found"}
        if not _has_org_access(current_user, fp["orgId"]):
            logger.info("Access denied: user %s not in org %s", current_user["id"], fp["orgId"])
            return 403, {"detail": "Not a member of this organization"}
        update_fund_property(fp_id, body)
        logger.info("Fund-property %s updated", fp_id)
        return 200, {"detail": "Fund-property updated"}
    except Exception as e:
        logger.error("Failed to update fund-property %s: %s", fp_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def delete(fp_id, current_user):
    logger.info("Deleting fund-property %s by user %s", fp_id, current_user["id"])
    try:
        fp = find_fund_property_by_id(fp_id)
        if not fp:
            logger.info("Fund-property not found: %s", fp_id)
            return 404, {"detail": "Fund-property not found"}
        if not _has_org_access(current_user, fp["orgId"]):
            logger.info("Access denied: user %s not in org %s", current_user["id"], fp["orgId"])
            return 403, {"detail": "Not a member of this organization"}
        delete_fund_property(fp_id)
        logger.info("Fund-property %s deleted", fp_id)
        return 200, {"detail": "Fund-property deleted"}
    except Exception as e:
        logger.error("Failed to delete fund-property %s: %s", fp_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}
