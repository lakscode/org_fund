from app.models import find_user_by_email, create_user, create_organization, add_user_to_org, get_user_orgs, list_organizations
from app.auth import hash_password, verify_password, create_access_token
from app.logger import get_logger

logger = get_logger("routes.auth")


def register(body):
    email = body.get("email")
    name = body.get("name")
    password = body.get("password")

    logger.info("Register attempt: email=%s, name=%s", email, name)

    if not all([email, name, password]):
        logger.info("Registration failed: missing required fields")
        return 400, {"detail": "Missing required fields"}

    if find_user_by_email(email):
        logger.info("Registration failed: email already registered - %s", email)
        return 400, {"detail": "Email already registered"}

    try:
        user_id = create_user(email, name, hash_password(password))
        logger.info("User created: id=%s, email=%s", user_id, email)

        org_id = create_organization(f"{name}'s Org")
        logger.info("Default org created: id=%s for user %s", org_id, user_id)

        add_user_to_org(user_id, org_id)
        logger.info("User %s added to org %s", user_id, org_id)

        token = create_access_token({"sub": user_id})
        logger.info("Registration complete for email=%s", email)
        return 200, {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        logger.error("Registration failed for email=%s: %s", email, e, exc_info=True)
        return 500, {"detail": "Internal server error"}


def login(body):
    email = body.get("email")
    password = body.get("password")

    logger.info("Login attempt: email=%s", email)

    if not all([email, password]):
        logger.info("Login failed: missing required fields")
        return 400, {"detail": "Missing required fields"}

    user = find_user_by_email(email)
    if not user:
        logger.info("Login failed: user not found - %s", email)
        return 401, {"detail": "Invalid email or password"}

    if not verify_password(password, user["hashed_password"]):
        logger.info("Login failed: wrong password for %s", email)
        return 401, {"detail": "Invalid email or password"}

    token = create_access_token({"sub": user["id"]})
    logger.info("Login successful: email=%s, user_id=%s", email, user["id"])
    return 200, {"access_token": token, "token_type": "bearer"}


def me(current_user):
    user_id = current_user["id"]
    logger.info("Fetching profile for user id=%s", user_id)
    try:
        orgs = get_user_orgs(current_user)
        logger.info("Profile fetched for user id=%s (%d orgs)", user_id, len(orgs))
        is_super = current_user.get("isSuperAdmin", False)
        # Super admin sees all orgs
        if is_super:
            all_orgs = list_organizations()
            for o in all_orgs:
                o["role"] = "admin"
            orgs = all_orgs

        return 200, {
            "id": current_user["id"],
            "email": current_user["email"],
            "name": current_user["name"],
            "isSuperAdmin": is_super,
            "orgs": orgs,
        }
    except Exception as e:
        logger.error("Failed to fetch profile for user id=%s: %s", user_id, e, exc_info=True)
        return 500, {"detail": "Internal server error"}
