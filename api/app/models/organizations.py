from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from app.database import organizations_col
from app.logger import get_logger

logger = get_logger("models.organizations")


def _now():
    return datetime.now(timezone.utc)


def serialize_org(doc):
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "status": doc.get("status", "active"),
        "createdAt": doc.get("createdAt", ""),
        "updatedAt": doc.get("updatedAt", ""),
    }


def create_organization(name, status="active"):
    logger.info("Creating organization: name=%s", name)
    now = _now()
    try:
        result = organizations_col.insert_one({
            "name": name,
            "status": status,
            "createdAt": now,
            "updatedAt": now,
        })
        logger.info("Organization created: id=%s, name=%s", result.inserted_id, name)
        return str(result.inserted_id)
    except Exception as e:
        logger.error("Failed to create organization name=%s: %s", name, e, exc_info=True)
        raise


def find_organization_by_id(org_id):
    logger.info("Looking up organization by id: %s", org_id)
    try:
        doc = organizations_col.find_one({"_id": ObjectId(org_id)})
    except InvalidId:
        logger.error("Invalid organization id format: %s", org_id)
        return None
    if doc:
        logger.info("Organization found: id=%s, name=%s", org_id, doc["name"])
    else:
        logger.info("No organization found for id: %s", org_id)
    return serialize_org(doc)


def find_organization_by_name(name):
    logger.info("Looking up organization by name: %s", name)
    doc = organizations_col.find_one({"name": name})
    if doc:
        logger.info("Organization found: name=%s, id=%s", name, doc["_id"])
    else:
        logger.info("No organization found for name: %s", name)
    return serialize_org(doc)


def list_organizations(status=None):
    logger.info("Listing organizations (status=%s)", status)
    query = {}
    if status:
        query["status"] = status
    docs = organizations_col.find(query).sort("name", 1)
    result = [serialize_org(d) for d in docs]
    logger.info("Found %d organizations", len(result))
    return result


def get_user_orgs(user):
    user_id = user.get("id", "unknown")
    org_roles = user.get("org_roles", [])
    org_ids = user.get("org_ids", [])
    logger.info("Fetching orgs for user %s (%d org_ids)", user_id, len(org_ids))
    try:
        oid_list = [ObjectId(oid) for oid in org_ids if oid]
        docs = organizations_col.find({"_id": {"$in": oid_list}})
        role_map = {r["org_id"]: r["role"] for r in org_roles}
        result = []
        for d in docs:
            org = serialize_org(d)
            org["role"] = role_map.get(org["id"], "member")
            result.append(org)
        logger.info("Fetched %d orgs for user %s", len(result), user_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch orgs for user %s: %s", user_id, e, exc_info=True)
        raise


def update_organization(org_id, updates):
    logger.info("Updating organization %s: fields=%s", org_id, list(updates.keys()))
    try:
        updates["updatedAt"] = _now()
        result = organizations_col.update_one(
            {"_id": ObjectId(org_id)},
            {"$set": updates},
        )
        if result.matched_count:
            logger.info("Organization %s updated successfully", org_id)
        else:
            logger.info("Organization %s not found for update", org_id)
        return result.matched_count > 0
    except Exception as e:
        logger.error("Failed to update organization %s: %s", org_id, e, exc_info=True)
        raise


def delete_organization(org_id):
    logger.info("Deleting organization %s", org_id)
    try:
        result = organizations_col.delete_one({"_id": ObjectId(org_id)})
        if result.deleted_count:
            logger.info("Organization %s deleted", org_id)
        else:
            logger.info("Organization %s not found for deletion", org_id)
        return result.deleted_count > 0
    except Exception as e:
        logger.error("Failed to delete organization %s: %s", org_id, e, exc_info=True)
        raise
