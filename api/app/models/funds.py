from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from app.database import funds_col
from app.logger import get_logger

logger = get_logger("models.funds")


def _now():
    return datetime.now(timezone.utc)


def serialize_fund(doc):
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "orgId": str(doc["orgId"]),
        "externalIds": doc.get("externalIds", []),
        "fundCode": doc.get("fundCode", ""),
        "fundName": doc.get("fundName", ""),
        "fundType": doc.get("fundType", ""),
        "vintageYear": doc.get("vintageYear"),
        "baseCurrency": doc.get("baseCurrency", "USD"),
        "status": doc.get("status", "active"),
        "managers": doc.get("managers", []),
        "settings": doc.get("settings", {}),
        "createdAt": doc.get("createdAt", ""),
        "updatedAt": doc.get("updatedAt", ""),
    }


def create_fund(org_id, data):
    logger.info("Creating fund: orgId=%s, fundCode=%s, fundName=%s", org_id, data.get("fundCode"), data.get("fundName"))
    now = _now()
    doc = {
        "orgId": org_id,
        "externalIds": data.get("externalIds", []),
        "fundCode": data["fundCode"],
        "fundName": data["fundName"],
        "fundType": data.get("fundType", ""),
        "vintageYear": data.get("vintageYear"),
        "baseCurrency": data.get("baseCurrency", "USD"),
        "status": data.get("status", "active"),
        "managers": data.get("managers", []),
        "settings": data.get("settings", {}),
        "createdAt": now,
        "updatedAt": now,
    }
    try:
        result = funds_col.insert_one(doc)
        logger.info("Fund created: id=%s", result.inserted_id)
        return str(result.inserted_id)
    except Exception as e:
        logger.error("Failed to create fund orgId=%s, fundCode=%s: %s", org_id, data.get("fundCode"), e)
        raise


def find_fund_by_id(fund_id):
    logger.info("Looking up fund by id: %s", fund_id)
    try:
        doc = funds_col.find_one({"_id": ObjectId(fund_id)})
    except InvalidId:
        logger.error("Invalid fund id format: %s", fund_id)
        return None
    if doc:
        logger.info("Fund found: id=%s, fundCode=%s", fund_id, doc.get("fundCode"))
    else:
        logger.info("No fund found for id: %s", fund_id)
    return serialize_fund(doc)


def list_funds_by_org(org_id, status=None):
    logger.info("Listing funds for org %s (status=%s)", org_id, status)
    query = {"orgId": org_id}
    if status:
        query["status"] = status
    try:
        docs = funds_col.find(query).sort("fundCode", 1)
        result = [serialize_fund(d) for d in docs]
        logger.info("Found %d funds for org %s", len(result), org_id)
        return result
    except Exception as e:
        logger.error("Failed to list funds for org %s: %s", org_id, e)
        raise


def update_fund(fund_id, updates):
    logger.info("Updating fund %s: fields=%s", fund_id, list(updates.keys()))
    try:
        updates["updatedAt"] = _now()
        result = funds_col.update_one(
            {"_id": ObjectId(fund_id)},
            {"$set": updates},
        )
        if result.matched_count:
            logger.info("Fund %s updated successfully", fund_id)
        else:
            logger.info("Fund %s not found for update", fund_id)
        return result.matched_count > 0
    except Exception as e:
        logger.error("Failed to update fund %s: %s", fund_id, e)
        raise


def delete_fund(fund_id):
    logger.info("Deleting fund %s", fund_id)
    try:
        result = funds_col.delete_one({"_id": ObjectId(fund_id)})
        if result.deleted_count:
            logger.info("Fund %s deleted", fund_id)
        else:
            logger.info("Fund %s not found for deletion", fund_id)
        return result.deleted_count > 0
    except Exception as e:
        logger.error("Failed to delete fund %s: %s", fund_id, e)
        raise


def find_fund_by_external_id(org_id, system, external_id):
    logger.info("Looking up fund by externalId: orgId=%s, system=%s, id=%s", org_id, system, external_id)
    doc = funds_col.find_one({
        "orgId": org_id,
        "externalIds": {"$elemMatch": {"system": system, "id": external_id}},
    })
    if doc:
        logger.info("Fund found via externalId: id=%s", doc["_id"])
    else:
        logger.info("No fund found for externalId system=%s, id=%s", system, external_id)
    return serialize_fund(doc)
