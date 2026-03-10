from app.models import (
    create_property, find_property_by_id, list_properties_by_org,
    list_properties_by_fund, update_property, delete_property,
    get_noi_vs_budget_by_org,
)
from app.database import tenants_col, units_col
from app.logger import get_logger

logger = get_logger("routes.properties")


def _has_org_access(user, org_id):
    if user.get("isSuperAdmin"):
        return True
    return org_id in user.get("org_ids", [])


def list_properties(org_id, current_user, query_params=None):
    logger.info("Listing properties for org %s by user %s", org_id, current_user["id"])
    if not _has_org_access(current_user, org_id):
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

        # Get occupancy data: tenant count and unit count per property
        prop_ids = [p["id"] for p in props]
        tenant_pipeline = [
            {"$match": {"propertyId": {"$in": prop_ids}}},
            {"$group": {"_id": "$propertyId", "count": {"$sum": 1}}},
        ]
        unit_pipeline = [
            {"$match": {"propertyId": {"$in": prop_ids}}},
            {"$group": {"_id": "$propertyId", "count": {"$sum": 1}}},
        ]
        tenant_counts = {r["_id"]: r["count"] for r in tenants_col.aggregate(tenant_pipeline)}
        unit_counts = {r["_id"]: r["count"] for r in units_col.aggregate(unit_pipeline)}

        for p in props:
            noi = noi_map.get(p.get("propertyCode"), {})
            p["noiActual"] = noi.get("noiActual", 0)
            p["noiBudget"] = noi.get("noiBudget", 0)
            p["noiVariance"] = noi.get("noiVariance", 0)

            # Occupancy
            units = unit_counts.get(p["id"], 0)
            tenants = tenant_counts.get(p["id"], 0)
            p["occupancy"] = round((tenants / units * 100), 1) if units > 0 else 0

            # DSCR placeholder (property-level DSCR from NOI / debt service)
            p["dscr"] = 0

            # NOI vs Budget percentage
            p["noiVsBudgetPct"] = round(((noi.get("noiActual", 0) / noi.get("noiBudget", 1)) * 100 - 100), 1) if noi.get("noiBudget") else 0
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
        if not _has_org_access(current_user, prop["orgId"]):
            logger.info("Access denied: user %s not in org %s", current_user["id"], prop["orgId"])
            return 403, {"detail": "Not a member of this organization"}
        logger.info("Property fetched: %s", property_id)
        return 200, prop
    except Exception as e:
        logger.error("Failed to get property %s: %s", property_id, e)
        return 500, {"detail": "Internal server error"}


def create(org_id, body, current_user):
    logger.info("Creating property in org %s by user %s", org_id, current_user["id"])
    if not _has_org_access(current_user, org_id):
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
        if not _has_org_access(current_user, prop["orgId"]):
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
        if not _has_org_access(current_user, prop["orgId"]):
            logger.info("Access denied: user %s not in org %s", current_user["id"], prop["orgId"])
            return 403, {"detail": "Not a member of this organization"}
        delete_property(property_id)
        logger.info("Property %s deleted", property_id)
        return 200, {"detail": "Property deleted"}
    except Exception as e:
        logger.error("Failed to delete property %s: %s", property_id, e)
        return 500, {"detail": "Internal server error"}
