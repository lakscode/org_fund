from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from app.database import properties_col
from app.logger import get_logger

logger = get_logger("models.properties")


def _now():
    return datetime.now(timezone.utc)


def serialize_property(doc):
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "orgId": str(doc["orgId"]),
        "externalIds": doc.get("externalIds", []),
        "propertyCode": doc.get("propertyCode", ""),
        "propertyName": doc.get("propertyName", ""),
        "address": doc.get("address", {}),
        "market": doc.get("market", ""),
        "propertyType": doc.get("propertyType", ""),
        "status": doc.get("status", "active"),
        "acquisitionDate": doc.get("acquisitionDate"),
        "fundIds": [str(fid) for fid in doc.get("fundIds", [])],
        "ownership": doc.get("ownership", {}),
        "metadata": doc.get("metadata", {}),
        "createdAt": doc.get("createdAt", ""),
        "updatedAt": doc.get("updatedAt", ""),
    }


def create_property(org_id, data):
    logger.info("Creating property: orgId=%s, propertyCode=%s, propertyName=%s", org_id, data.get("propertyCode"), data.get("propertyName"))
    now = _now()
    fund_ids = [fid for fid in data.get("fundIds", [])]
    doc = {
        "orgId": org_id,
        "externalIds": data.get("externalIds", []),
        "propertyCode": data["propertyCode"],
        "propertyName": data["propertyName"],
        "address": data.get("address", {}),
        "market": data.get("market", ""),
        "propertyType": data.get("propertyType", ""),
        "status": data.get("status", "active"),
        "acquisitionDate": data.get("acquisitionDate"),
        "fundIds": fund_ids,
        "ownership": data.get("ownership", {}),
        "metadata": data.get("metadata", {}),
        "createdAt": now,
        "updatedAt": now,
    }
    try:
        result = properties_col.insert_one(doc)
        logger.info("Property created: id=%s", result.inserted_id)
        return str(result.inserted_id)
    except Exception as e:
        logger.error("Failed to create property orgId=%s, propertyCode=%s: %s", org_id, data.get("propertyCode"), e)
        raise


def find_property_by_id(property_id):
    logger.info("Looking up property by id: %s", property_id)
    try:
        doc = properties_col.find_one({"_id": ObjectId(property_id)})
    except InvalidId:
        logger.error("Invalid property id format: %s", property_id)
        return None
    if doc:
        logger.info("Property found: id=%s, propertyCode=%s", property_id, doc.get("propertyCode"))
    else:
        logger.info("No property found for id: %s", property_id)
    return serialize_property(doc)


def list_properties_by_org(org_id, status=None, property_type=None, market=None):
    logger.info("Listing properties for org %s (status=%s, type=%s, market=%s)", org_id, status, property_type, market)
    query = {"orgId": org_id}
    if status:
        query["status"] = status
    if property_type:
        query["propertyType"] = property_type
    if market:
        query["market"] = market
    try:
        docs = properties_col.find(query).sort("propertyCode", 1)
        result = [serialize_property(d) for d in docs]
        logger.info("Found %d properties for org %s", len(result), org_id)
        return result
    except Exception as e:
        logger.error("Failed to list properties for org %s: %s", org_id, e)
        raise


def list_properties_by_fund(fund_id):
    logger.info("Listing properties for fund %s", fund_id)
    try:
        docs = properties_col.find({"fundIds": fund_id}).sort("propertyCode", 1)
        result = [serialize_property(d) for d in docs]
        logger.info("Found %d properties for fund %s", len(result), fund_id)
        return result
    except Exception as e:
        logger.error("Failed to list properties for fund %s: %s", fund_id, e)
        raise


def update_property(property_id, updates):
    logger.info("Updating property %s: fields=%s", property_id, list(updates.keys()))
    try:
        if "fundIds" in updates:
            updates["fundIds"] = [fid for fid in updates["fundIds"]]
        updates["updatedAt"] = _now()
        result = properties_col.update_one(
            {"_id": ObjectId(property_id)},
            {"$set": updates},
        )
        if result.matched_count:
            logger.info("Property %s updated successfully", property_id)
        else:
            logger.info("Property %s not found for update", property_id)
        return result.matched_count > 0
    except Exception as e:
        logger.error("Failed to update property %s: %s", property_id, e)
        raise


def delete_property(property_id):
    logger.info("Deleting property %s", property_id)
    try:
        result = properties_col.delete_one({"_id": ObjectId(property_id)})
        if result.deleted_count:
            logger.info("Property %s deleted", property_id)
        else:
            logger.info("Property %s not found for deletion", property_id)
        return result.deleted_count > 0
    except Exception as e:
        logger.error("Failed to delete property %s: %s", property_id, e)
        raise


def find_property_by_external_id(org_id, system, external_id):
    logger.info("Looking up property by externalId: orgId=%s, system=%s, id=%s", org_id, system, external_id)
    doc = properties_col.find_one({
        "orgId": org_id,
        "externalIds": {"$elemMatch": {"system": system, "id": external_id}},
    })
    if doc:
        logger.info("Property found via externalId: id=%s", doc["_id"])
    else:
        logger.info("No property found for externalId system=%s, id=%s", system, external_id)
    return serialize_property(doc)
