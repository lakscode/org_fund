from app.models import (
    list_organizations, create_organization, find_organization_by_id,
    update_organization, delete_organization,
    list_all_users, find_user_by_email, find_user_by_id,
    create_user, add_user_to_org, update_user, remove_user_from_org,
)
from app.auth import hash_password
from app.logger import get_logger

logger = get_logger("routes.superadmin")


def _require_super(current_user):
    """Return error tuple if user is not a super admin, else None."""
    if not current_user.get("isSuperAdmin"):
        return 403, {"detail": "Super admin access required"}
    return None


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------

def sa_list_orgs(current_user):
    """List ALL organizations."""
    err = _require_super(current_user)
    if err:
        return err
    try:
        orgs = list_organizations()
        return 200, orgs
    except Exception as e:
        logger.error("SA list orgs failed: %s", e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def sa_create_org(body, current_user):
    """Create a new organization."""
    err = _require_super(current_user)
    if err:
        return err
    name = body.get("name")
    if not name:
        return 400, {"detail": "name is required"}
    try:
        org_id = create_organization(name, body.get("status", "active"))
        logger.info("SA created org: id=%s name=%s", org_id, name)
        return 201, {"id": org_id, "detail": "Organization created"}
    except Exception as e:
        logger.error("SA create org failed: %s", e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def sa_update_org(org_id, body, current_user):
    """Update an organization."""
    err = _require_super(current_user)
    if err:
        return err
    try:
        updated = update_organization(org_id, body)
        if not updated:
            return 404, {"detail": "Organization not found"}
        return 200, {"detail": "Organization updated"}
    except Exception as e:
        logger.error("SA update org %s failed: %s", org_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def sa_delete_org(org_id, current_user):
    """Delete an organization."""
    err = _require_super(current_user)
    if err:
        return err
    try:
        deleted = delete_organization(org_id)
        if not deleted:
            return 404, {"detail": "Organization not found"}
        return 200, {"detail": "Organization deleted"}
    except Exception as e:
        logger.error("SA delete org %s failed: %s", org_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def sa_list_users(current_user):
    """List ALL users in the system."""
    err = _require_super(current_user)
    if err:
        return err
    try:
        users = list_all_users()
        return 200, users
    except Exception as e:
        logger.error("SA list users failed: %s", e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def sa_create_user(body, current_user):
    """Create a new user and optionally map to orgs."""
    err = _require_super(current_user)
    if err:
        return err

    email = body.get("email")
    name = body.get("name")
    password = body.get("password", "changeme123")
    org_mappings = body.get("orgs", [])  # [{"org_id": "...", "role": "admin"}, ...]

    if not email or not name:
        return 400, {"detail": "email and name are required"}

    existing = find_user_by_email(email)
    if existing:
        return 409, {"detail": "Email already registered"}

    try:
        user_id = create_user(email, name, hash_password(password))
        logger.info("SA created user: id=%s email=%s", user_id, email)

        for mapping in org_mappings:
            oid = mapping.get("org_id")
            role = mapping.get("role", "member")
            if oid:
                add_user_to_org(user_id, oid, role)
                logger.info("SA mapped user %s to org %s as %s", user_id, oid, role)

        return 201, {"id": user_id, "detail": "User created"}
    except Exception as e:
        logger.error("SA create user failed: %s", e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def sa_update_user(user_id, body, current_user):
    """Update user fields (name, email, password)."""
    err = _require_super(current_user)
    if err:
        return err

    target = find_user_by_id(user_id)
    if not target:
        return 404, {"detail": "User not found"}

    try:
        updates = {}
        if "name" in body:
            updates["name"] = body["name"]
        if "email" in body:
            updates["email"] = body["email"]
        if "password" in body:
            updates["hashed_password"] = hash_password(body["password"])
        if updates:
            update_user(user_id, updates)
        return 200, {"detail": "User updated"}
    except Exception as e:
        logger.error("SA update user %s failed: %s", user_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def sa_map_user_to_org(body, current_user):
    """Add a user to one or more organizations."""
    err = _require_super(current_user)
    if err:
        return err

    user_id = body.get("userId")
    org_mappings = body.get("orgs", [])  # [{"org_id": "...", "role": "admin"}, ...]

    if not user_id or not org_mappings:
        return 400, {"detail": "userId and orgs are required"}

    target = find_user_by_id(user_id)
    if not target:
        return 404, {"detail": "User not found"}

    try:
        added = []
        for mapping in org_mappings:
            oid = mapping.get("org_id")
            role = mapping.get("role", "member")
            if not oid:
                continue
            org = find_organization_by_id(oid)
            if not org:
                continue
            if oid in target.get("org_ids", []):
                continue  # already a member
            add_user_to_org(user_id, oid, role)
            added.append(oid)
            logger.info("SA mapped user %s to org %s as %s", user_id, oid, role)

        return 200, {"detail": f"User mapped to {len(added)} org(s)", "added": added}
    except Exception as e:
        logger.error("SA map user failed: %s", e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def sa_remove_user_from_org(body, current_user):
    """Remove a user from an organization."""
    err = _require_super(current_user)
    if err:
        return err

    user_id = body.get("userId")
    org_id = body.get("orgId")

    if not user_id or not org_id:
        return 400, {"detail": "userId and orgId are required"}

    target = find_user_by_id(user_id)
    if not target:
        return 404, {"detail": "User not found"}

    try:
        remove_user_from_org(user_id, org_id)
        return 200, {"detail": "User removed from organization"}
    except Exception as e:
        logger.error("SA remove user from org failed: %s", e, exc_info=True)
        return 500, {"detail": "Internal server error"}
