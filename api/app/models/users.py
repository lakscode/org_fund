from bson import ObjectId
from bson.errors import InvalidId
from app.database import users_col
from app.logger import get_logger

logger = get_logger("models.users")


def serialize_user(doc):
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "email": doc["email"],
        "name": doc["name"],
        "hashed_password": doc.get("hashed_password", ""),
        "org_ids": doc.get("org_ids", []),
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
        })
        logger.info("User created successfully: id=%s", result.inserted_id)
        return str(result.inserted_id)
    except Exception as e:
        logger.error("Failed to create user email=%s: %s", email, e)
        raise


def add_user_to_org(user_id, org_id):
    logger.info("Adding user %s to org %s", user_id, org_id)
    try:
        users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"org_ids": org_id}},
        )
        logger.info("User %s added to org %s successfully", user_id, org_id)
    except Exception as e:
        logger.error("Failed to add user %s to org %s: %s", user_id, org_id, e)
        raise


def get_org_members(org_id):
    logger.info("Fetching members for org %s", org_id)
    try:
        docs = users_col.find({"org_ids": org_id})
        result = [
            {"id": str(d["_id"]), "email": d["email"], "name": d["name"]}
            for d in docs
        ]
        logger.info("Found %d members for org %s", len(result), org_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch members for org %s: %s", org_id, e)
        raise
