from app.models import (
    find_organization_by_id, get_user_orgs, get_org_members,
    create_organization, update_organization, delete_organization,
    find_user_by_email, find_user_by_id, create_user, add_user_to_org, update_user,
)
from app.auth import hash_password
from app.logger import get_logger

logger = get_logger("routes.orgs")


def list_user_orgs(current_user):
    user_id = current_user["id"]
    logger.info("Listing orgs for user id=%s", user_id)
    try:
        orgs = get_user_orgs(current_user)
        logger.info("Found %d orgs for user id=%s", len(orgs), user_id)
        return 200, orgs
    except Exception as e:
        logger.error("Failed to list orgs for user id=%s: %s", user_id, e)
        return 500, {"detail": "Internal server error"}


def get_org_data(org_id, current_user):
    user_id = current_user["id"]
    logger.info("Fetching org data: org_id=%s, user_id=%s", org_id, user_id)

    try:
        org = find_organization_by_id(org_id)
        if not org:
            logger.info("Org not found: org_id=%s", org_id)
            return 404, {"detail": "Organization not found"}

        user_org_ids = current_user.get("org_ids", [])
        if org["id"] not in user_org_ids:
            logger.info("Access denied: user %s not a member of org %s", user_id, org_id)
            return 403, {"detail": "Not a member of this organization"}

        members = get_org_members(org_id)
        logger.info("Org data fetched: org_id=%s, %d members", org_id, len(members))
        return 200, {
            "org": org,
            "members": members,
        }
    except Exception as e:
        logger.error("Failed to fetch org data org_id=%s: %s", org_id, e)
        return 500, {"detail": "Internal server error"}


def create_org(body, current_user):
    name = body.get("name")
    logger.info("Creating org: name=%s by user %s", name, current_user["id"])
    if not name:
        logger.info("Create org failed: missing name")
        return 400, {"detail": "name is required"}
    try:
        org_id = create_organization(name, body.get("status", "active"))
        logger.info("Org created: id=%s", org_id)
        return 201, {"id": org_id}
    except Exception as e:
        logger.error("Failed to create org name=%s: %s", name, e)
        return 500, {"detail": "Internal server error"}


def update_org(org_id, body, current_user):
    logger.info("Updating org %s by user %s", org_id, current_user["id"])
    user_org_ids = current_user.get("org_ids", [])
    if org_id not in user_org_ids:
        logger.info("Access denied: user %s not in org %s", current_user["id"], org_id)
        return 403, {"detail": "Not a member of this organization"}
    try:
        updated = update_organization(org_id, body)
        if not updated:
            return 404, {"detail": "Organization not found"}
        logger.info("Org %s updated", org_id)
        return 200, {"detail": "Organization updated"}
    except Exception as e:
        logger.error("Failed to update org %s: %s", org_id, e)
        return 500, {"detail": "Internal server error"}


def delete_org(org_id, current_user):
    logger.info("Deleting org %s by user %s", org_id, current_user["id"])
    user_org_ids = current_user.get("org_ids", [])
    if org_id not in user_org_ids:
        logger.info("Access denied: user %s not in org %s", current_user["id"], org_id)
        return 403, {"detail": "Not a member of this organization"}
    try:
        deleted = delete_organization(org_id)
        if not deleted:
            return 404, {"detail": "Organization not found"}
        logger.info("Org %s deleted", org_id)
        return 200, {"detail": "Organization deleted"}
    except Exception as e:
        logger.error("Failed to delete org %s: %s", org_id, e)
        return 500, {"detail": "Internal server error"}


def add_member(org_id, body, current_user):
    """Add an existing or new user to an organization."""
    logger.info("Adding member to org %s by user %s", org_id, current_user["id"])

    user_org_ids = current_user.get("org_ids", [])
    if org_id not in user_org_ids:
        return 403, {"detail": "Not a member of this organization"}

    email = body.get("email")
    name = body.get("name", "")
    role = body.get("role", "member")

    if not email:
        return 400, {"detail": "email is required"}

    try:
        user = find_user_by_email(email)
        if user:
            if org_id in user.get("org_ids", []):
                return 409, {"detail": "User is already a member of this organization"}
            add_user_to_org(user["id"], org_id, role)
            logger.info("Existing user %s added to org %s", user["id"], org_id)
            return 200, {"detail": "User added to organization", "userId": user["id"]}
        else:
            if not name:
                return 400, {"detail": "name is required for new users"}
            password = body.get("password", "changeme123")
            user_id = create_user(email, name, hash_password(password))
            add_user_to_org(user_id, org_id, role)
            logger.info("New user %s created and added to org %s", user_id, org_id)
            return 201, {"detail": "User created and added to organization", "userId": user_id}
    except Exception as e:
        logger.error("Failed to add member to org %s: %s", org_id, e)
        return 500, {"detail": "Internal server error"}


def edit_member(org_id, user_id, body, current_user):
    """Edit a member's name, email, or role within an org."""
    logger.info("Editing member %s in org %s by user %s", user_id, org_id, current_user["id"])

    if org_id not in current_user.get("org_ids", []):
        return 403, {"detail": "Not a member of this organization"}

    target = find_user_by_id(user_id)
    if not target or org_id not in target.get("org_ids", []):
        return 404, {"detail": "User not found in this organization"}

    try:
        updates = {}
        if "name" in body:
            updates["name"] = body["name"]
        if "email" in body:
            updates["email"] = body["email"]
        if "role" in body:
            updates["role"] = body["role"]
            updates["org_id"] = org_id
        if not updates:
            return 400, {"detail": "No fields to update"}
        update_user(user_id, updates)
        return 200, {"detail": "User updated"}
    except Exception as e:
        logger.error("Failed to edit member %s in org %s: %s", user_id, org_id, e)
        return 500, {"detail": "Internal server error"}


def reset_member_password(org_id, user_id, body, current_user):
    """Reset a member's password."""
    logger.info("Resetting password for user %s in org %s by user %s", user_id, org_id, current_user["id"])

    if org_id not in current_user.get("org_ids", []):
        return 403, {"detail": "Not a member of this organization"}

    target = find_user_by_id(user_id)
    if not target or org_id not in target.get("org_ids", []):
        return 404, {"detail": "User not found in this organization"}

    new_password = body.get("password", "")
    if len(new_password) < 6:
        return 400, {"detail": "Password must be at least 6 characters"}

    try:
        update_user(user_id, {"hashed_password": hash_password(new_password)})
        return 200, {"detail": "Password reset successfully"}
    except Exception as e:
        logger.error("Failed to reset password for user %s: %s", user_id, e)
        return 500, {"detail": "Internal server error"}
