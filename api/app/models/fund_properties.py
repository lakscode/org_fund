from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from app.database import fund_properties_col
from app.logger import get_logger

logger = get_logger("models.fund_properties")


def _now():
    return datetime.now(timezone.utc)


def serialize_fund_property(doc):
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "orgId": str(doc["orgId"]),
        "fundId": str(doc["fundId"]),
        "propertyId": str(doc["propertyId"]),
        "startDate": doc.get("startDate"),
        "endDate": doc.get("endDate"),
        "ownershipPct": doc.get("ownershipPct"),
        "role": doc.get("role", "primary"),
    }


def create_fund_property(org_id, data):
    logger.info("Creating fund-property link: orgId=%s, fundId=%s, propertyId=%s",
                org_id, data.get("fundId"), data.get("propertyId"))
    doc = {
        "orgId": org_id,
        "fundId": data["fundId"],
        "propertyId": data["propertyId"],
        "startDate": data.get("startDate"),
        "endDate": data.get("endDate"),
        "ownershipPct": data.get("ownershipPct"),
        "role": data.get("role", "primary"),
    }
    try:
        result = fund_properties_col.insert_one(doc)
        logger.info("Fund-property link created: id=%s", result.inserted_id)
        return str(result.inserted_id)
    except Exception as e:
        logger.error("Failed to create fund-property link: %s", e, exc_info=True)
        raise


def find_fund_property_by_id(fp_id):
    logger.info("Looking up fund-property by id: %s", fp_id)
    try:
        doc = fund_properties_col.find_one({"_id": ObjectId(fp_id)})
    except InvalidId:
        logger.error("Invalid fund-property id format: %s", fp_id)
        return None
    if doc:
        logger.info("Fund-property found: id=%s", fp_id)
    else:
        logger.info("No fund-property found for id: %s", fp_id)
    return serialize_fund_property(doc)


def list_by_fund(fund_id):
    logger.info("Listing fund-properties for fund %s", fund_id)
    try:
        docs = fund_properties_col.find({"fundId": fund_id})
        result = [serialize_fund_property(d) for d in docs]
        logger.info("Found %d fund-property links for fund %s", len(result), fund_id)
        return result
    except Exception as e:
        logger.error("Failed to list fund-properties for fund %s: %s", fund_id, e, exc_info=True)
        raise


def list_by_property(property_id):
    logger.info("Listing fund-properties for property %s", property_id)
    try:
        docs = fund_properties_col.find({"propertyId": property_id})
        result = [serialize_fund_property(d) for d in docs]
        logger.info("Found %d fund-property links for property %s", len(result), property_id)
        return result
    except Exception as e:
        logger.error("Failed to list fund-properties for property %s: %s", property_id, e, exc_info=True)
        raise


def list_by_org(org_id):
    logger.info("Listing all fund-properties for org %s", org_id)
    try:
        docs = fund_properties_col.find({"orgId": org_id})
        result = [serialize_fund_property(d) for d in docs]
        logger.info("Found %d fund-property links for org %s", len(result), org_id)
        return result
    except Exception as e:
        logger.error("Failed to list fund-properties for org %s: %s", org_id, e, exc_info=True)
        raise


def update_fund_property(fp_id, updates):
    logger.info("Updating fund-property %s: fields=%s", fp_id, list(updates.keys()))
    try:
        result = fund_properties_col.update_one(
            {"_id": ObjectId(fp_id)},
            {"$set": updates},
        )
        if result.matched_count:
            logger.info("Fund-property %s updated successfully", fp_id)
        else:
            logger.info("Fund-property %s not found for update", fp_id)
        return result.matched_count > 0
    except Exception as e:
        logger.error("Failed to update fund-property %s: %s", fp_id, e, exc_info=True)
        raise


def delete_fund_property(fp_id):
    logger.info("Deleting fund-property %s", fp_id)
    try:
        result = fund_properties_col.delete_one({"_id": ObjectId(fp_id)})
        if result.deleted_count:
            logger.info("Fund-property %s deleted", fp_id)
        else:
            logger.info("Fund-property %s not found for deletion", fp_id)
        return result.deleted_count > 0
    except Exception as e:
        logger.error("Failed to delete fund-property %s: %s", fp_id, e, exc_info=True)
        raise
