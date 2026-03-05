from app.models import (
    find_organization_by_id, get_user_orgs, get_org_members,
    create_organization, update_organization, delete_organization,
)
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
