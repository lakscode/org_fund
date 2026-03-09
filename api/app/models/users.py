from bson import ObjectId
from bson.errors import InvalidId
from app.database import users_col
from app.logger import get_logger

logger = get_logger("models.users")


def _get_org_roles(doc):
    """Return org_roles list, migrating from legacy org_ids if needed."""
    if "org_roles" in doc and doc["org_roles"]:
        return doc["org_roles"]
    # Legacy: flat org_ids list -> convert with default role
    return [{"org_id": oid, "role": "member"} for oid in doc.get("org_ids", [])]


def serialize_user(doc):
    if not doc:
        return None
    org_roles = _get_org_roles(doc)
    return {
        "id": str(doc["_id"]),
        "email": doc["email"],
        "name": doc["name"],
        "hashed_password": doc.get("hashed_password", ""),
        "org_ids": [r["org_id"] for r in org_roles],
        "org_roles": org_roles,
    }


def find_user_by_email(email):
    logger.info("Looking up user by email: %s", email)
    doc = users_col.find_one({"email": email})
    if doc:
        logger.info("User found for email: %s (id=%s)", email, doc["_id"])
    else:
        logger.info("No user found for email: %s", email)
    return serialize_user(doc)


def find_user_by_id(user_id):
    logger.info("Looking up user by id: %s", user_id)
    try:
        doc = users_col.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        logger.error("Invalid user id format: %s", user_id)
        return None
    if doc:
        logger.info("User found: id=%s, email=%s", user_id, doc["email"])
    else:
        logger.info("No user found for id: %s", user_id)
    return serialize_user(doc)


def create_user(email, name, hashed_password):
    logger.info("Creating user: email=%s, name=%s", email, name)
    try:
        result = users_col.insert_one({
            "email": email,
            "name": name,
            "hashed_password": hashed_password,
            "org_ids": [],
            "org_roles": [],
        })
        logger.info("User created successfully: id=%s", result.inserted_id)
        return str(result.inserted_id)
    except Exception as e:
        logger.error("Failed to create user email=%s: %s", email, e)
        raise


def add_user_to_org(user_id, org_id, role="member"):
    logger.info("Adding user %s to org %s with role %s", user_id, org_id, role)
    try:
        # Add to org_roles (new format)
        users_col.update_one(
            {"_id": ObjectId(user_id), "org_roles.org_id": {"$ne": org_id}},
            {"$push": {"org_roles": {"org_id": org_id, "role": role}}},
        )
        # Keep org_ids in sync for backward compat
        users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"org_ids": org_id}},
        )
        logger.info("User %s added to org %s with role %s", user_id, org_id, role)
    except Exception as e:
        logger.error("Failed to add user %s to org %s: %s", user_id, org_id, e)
        raise


def update_user(user_id, updates):
    """Update user fields (name, email) and optionally org role."""
    logger.info("Updating user %s with fields: %s", user_id, list(updates.keys()))
    try:
        set_fields = {}
        if "name" in updates:
            set_fields["name"] = updates["name"]
        if "email" in updates:
            set_fields["email"] = updates["email"]
        if "hashed_password" in updates:
            set_fields["hashed_password"] = updates["hashed_password"]

        if set_fields:
            users_col.update_one({"_id": ObjectId(user_id)}, {"$set": set_fields})

        # Update role within org_roles array
        if "role" in updates and "org_id" in updates:
            users_col.update_one(
                {"_id": ObjectId(user_id), "org_roles.org_id": updates["org_id"]},
                {"$set": {"org_roles.$.role": updates["role"]}},
            )
        logger.info("User %s updated", user_id)
        return True
    except Exception as e:
        logger.error("Failed to update user %s: %s", user_id, e)
        raise


def get_org_members(org_id):
    logger.info("Fetching members for org %s", org_id)
    try:
        docs = users_col.find({"org_ids": org_id})
        result = []
        for d in docs:
            org_roles = _get_org_roles(d)
            role_entry = next((r for r in org_roles if r["org_id"] == org_id), None)
            result.append({
                "id": str(d["_id"]),
                "email": d["email"],
                "name": d["name"],
                "role": role_entry["role"] if role_entry else "member",
                "createdAt": d["_id"].generation_time.isoformat(),
            })
        logger.info("Found %d members for org %s", len(result), org_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch members for org %s: %s", org_id, e)
        raise
