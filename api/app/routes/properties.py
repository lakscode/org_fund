from app.models import (
    create_property, find_property_by_id, list_properties_by_org,
    list_properties_by_fund, update_property, delete_property,
    get_noi_vs_budget_by_org,
)
from app.logger import get_logger

logger = get_logger("routes.properties")


def list_properties(org_id, current_user, query_params=None):
    logger.info("Listing properties for org %s by user %s", org_id, current_user["id"])
    if org_id not in current_user.get("org_ids", []):
        logger.info("Access denied: user %s not in org %s", current_user["id"], org_id)
        return 403, {"detail": "Not a member of this organization"}
    try:
        params = query_params or {}
        props = list_properties_by_org(
            org_id,
            status=params.get("status"),
            property_type=params.get("propertyType"),
            market=params.get("market"),
        )
        noi_map = get_noi_vs_budget_by_org(org_id)
        for p in props:
            noi = noi_map.get(p.get("propertyCode"), {})
            p["noiActual"] = noi.get("noiActual", 0)
            p["noiBudget"] = noi.get("noiBudget", 0)
            p["noiVariance"] = noi.get("noiVariance", 0)
        logger.info("Found %d properties for org %s", len(props), org_id)
        return 200, props
    except Exception as e:
        logger.error("Failed to list properties for org %s: %s", org_id, e)
        return 500, {"detail": "Internal server error"}


def list_by_fund(fund_id, current_user):
    logger.info("Listing properties for fund %s by user %s", fund_id, current_user["id"])
    try:
        props = list_properties_by_fund(fund_id)
        logger.info("Found %d properties for fund %s", len(props), fund_id)
        return 200, props
    except Exception as e:
        logger.error("Failed to list properties for fund %s: %s", fund_id, e)
        return 500, {"detail": "Internal server error"}


def get_property(property_id, current_user):
    logger.info("Getting property %s by user %s", property_id, current_user["id"])
    try:
        prop = find_property_by_id(property_id)
        if not prop:
            logger.info("Property not found: %s", property_id)
            return 404, {"detail": "Property not found"}
        if prop["orgId"] not in current_user.get("org_ids", []):
            logger.info("Access denied: user %s not in org %s", current_user["id"], prop["orgId"])
            return 403, {"detail": "Not a member of this organization"}
        logger.info("Property fetched: %s", property_id)
        return 200, prop
    except Exception as e:
        logger.error("Failed to get property %s: %s", property_id, e)
        return 500, {"detail": "Internal server error"}


def create(org_id, body, current_user):
    logger.info("Creating property in org %s by user %s", org_id, current_user["id"])
    if org_id not in current_user.get("org_ids", []):
        logger.info("Access denied: user %s not in org %s", current_user["id"], org_id)
        return 403, {"detail": "Not a member of this organization"}

    property_code = body.get("propertyCode")
    property_name = body.get("propertyName")
    if not property_code or not property_name:
        logger.info("Create property failed: missing propertyCode or propertyName")
        return 400, {"detail": "propertyCode and propertyName are required"}

    try:
        property_id = create_property(org_id, body)
        logger.info("Property created: id=%s in org %s", property_id, org_id)
        return 201, {"id": property_id}
    except Exception as e:
        logger.error("Failed to create property in org %s: %s", org_id, e)
        return 500, {"detail": "Internal server error"}


def update(property_id, body, current_user):
    logger.info("Updating property %s by user %s", property_id, current_user["id"])
    try:
        prop = find_property_by_id(property_id)
        if not prop:
            logger.info("Property not found: %s", property_id)
            return 404, {"detail": "Property not found"}
        if prop["orgId"] not in current_user.get("org_ids", []):
            logger.info("Access denied: user %s not in org %s", current_user["id"], prop["orgId"])
            return 403, {"detail": "Not a member of this organization"}
        update_property(property_id, body)
        logger.info("Property %s updated", property_id)
        return 200, {"detail": "Property updated"}
    except Exception as e:
        logger.error("Failed to update property %s: %s", property_id, e)
        return 500, {"detail": "Internal server error"}


def delete(property_id, current_user):
    logger.info("Deleting property %s by user %s", property_id, current_user["id"])
    try:
        prop = find_property_by_id(property_id)
        if not prop:
            logger.info("Property not found: %s", property_id)
            return 404, {"detail": "Property not found"}
        if prop["orgId"] not in current_user.get("org_ids", []):
            logger.info("Access denied: user %s not in org %s", current_user["id"], prop["orgId"])
            return 403, {"detail": "Not a member of this organization"}
        delete_property(property_id)
        logger.info("Property %s deleted", property_id)
        return 200, {"detail": "Property deleted"}
    except Exception as e:
        logger.error("Failed to delete property %s: %s", property_id, e)
        return 500, {"detail": "Internal server error"}
