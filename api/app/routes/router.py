import json
import os
import re
from urllib.parse import urlparse, parse_qs

from app.config import config
from app.auth import get_current_user
from app.routes import auth as auth_routes
from app.routes import orgs as org_routes
from app.routes import funds as fund_routes
from app.routes import properties as property_routes
from app.routes import fund_properties as fp_routes
from app.routes import balancesheet as bs_routes
from app.logger import get_logger

logger = get_logger("router")

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "templates")

_server_started = None

# Regex patterns for ID-based routes
RE_ORG = re.compile(r"^/api/orgs/([a-f0-9]{24})$")
RE_ORG_FUNDS = re.compile(r"^/api/orgs/([a-f0-9]{24})/funds/?$")
RE_FUND = re.compile(r"^/api/funds/([a-f0-9]{24})$")
RE_FUND_PROPERTIES = re.compile(r"^/api/funds/([a-f0-9]{24})/properties/?$")
RE_FUND_FUND_PROPS = re.compile(r"^/api/funds/([a-f0-9]{24})/fund-properties/?$")
RE_ORG_PROPERTIES = re.compile(r"^/api/orgs/([a-f0-9]{24})/properties/?$")
RE_PROPERTY = re.compile(r"^/api/properties/([a-f0-9]{24})$")
RE_PROPERTY_FUND_PROPS = re.compile(r"^/api/properties/([a-f0-9]{24})/fund-properties/?$")
RE_ORG_FUND_PROPS = re.compile(r"^/api/orgs/([a-f0-9]{24})/fund-properties/?$")
RE_FUND_PROP = re.compile(r"^/api/fund-properties/([a-f0-9]{24})$")
RE_FUND_BALANCESHEET = re.compile(r"^/api/funds/([^/]+)/balancesheet/?$")
RE_ORG_MEMBERS = re.compile(r"^/api/orgs/([a-f0-9]{24})/members/?$")
RE_ORG_MEMBER = re.compile(r"^/api/orgs/([a-f0-9]{24})/members/([a-f0-9]{24})$")
RE_ORG_MEMBER_RESET_PW = re.compile(r"^/api/orgs/([a-f0-9]{24})/members/([a-f0-9]{24})/reset-password$")


def set_server_started(ts):
    global _server_started
    _server_started = ts
    logger.info("Server started timestamp set: %s", ts)


def _load_template(name, **kwargs):
    path = os.path.join(TEMPLATES_DIR, name)
    logger.info("Loading template: %s", path)
    try:
        with open(path, encoding="utf-8") as f:
            html = f.read()
        logger.info("Template loaded successfully: %s", name)
        return html.format(**kwargs)
    except FileNotFoundError:
        logger.error("Template not found: %s", path)
        raise
    except Exception as e:
        logger.error("Failed to load template %s: %s", name, e)
        raise


def _require_auth(handler):
    auth_header = handler.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.info("Missing or invalid Authorization header")
        return None
    token = auth_header[7:]
    logger.info("Authenticating request with Bearer token")
    user = get_current_user(token)
    if user:
        logger.info("Request authenticated for user id=%s", user["id"])
    else:
        logger.info("Authentication failed: invalid token")
    return user


def _read_body(handler):
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        logger.info("Request body is empty")
        return {}
    logger.info("Reading request body: %d bytes", length)
    body = json.loads(handler.rfile.read(length))
    logger.info("Request body parsed successfully")
    return body


def _auth_or_401(handler):
    user = _require_auth(handler)
    if not user:
        return None, ("json", 401, {"detail": "Not authenticated"})
    return user, None


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------
def handle_get(handler):
    raw_path = handler.path
    parsed = urlparse(raw_path)
    path = parsed.path
    query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    logger.info("GET %s", raw_path)

    # Index page
    if path == "/":
        logger.info("Serving index page")
        html = _load_template(
            "index.html",
            app_name=config.APP_NAME,
            server_started=_server_started,
        )
        return "html", 200, html

    # Health
    if path == "/api/health":
        logger.info("Health check OK")
        return "json", 200, {"status": "ok"}

    # Auth: me
    if path == "/api/auth/me":
        user, err = _auth_or_401(handler)
        if err:
            return err
        status, data = auth_routes.me(user)
        logger.info("GET /api/auth/me -> %d", status)
        return "json", status, data

    # Orgs: list
    if path in ("/api/orgs", "/api/orgs/"):
        user, err = _auth_or_401(handler)
        if err:
            return err
        status, data = org_routes.list_user_orgs(user)
        logger.info("GET /api/orgs -> %d", status)
        return "json", status, data

    # Orgs: get one
    m = RE_ORG.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id = m.group(1)
        status, data = org_routes.get_org_data(org_id, user)
        logger.info("GET /api/orgs/%s -> %d", org_id, status)
        return "json", status, data

    # Funds: list by org
    m = RE_ORG_FUNDS.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id = m.group(1)
        status, data = fund_routes.list_funds(org_id, user)
        logger.info("GET /api/orgs/%s/funds -> %d", org_id, status)
        return "json", status, data

    # Funds: get one
    m = RE_FUND.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        fund_id = m.group(1)
        status, data = fund_routes.get_fund(fund_id, user)
        logger.info("GET /api/funds/%s -> %d", fund_id, status)
        return "json", status, data

    # Balance sheet: get by fund
    m = RE_FUND_BALANCESHEET.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        fund_id = m.group(1)
        status, data = bs_routes.get(fund_id, user)
        logger.info("GET /api/funds/%s/balancesheet -> %d", fund_id, status)
        return "json", status, data

    # Properties: list by org
    m = RE_ORG_PROPERTIES.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id = m.group(1)
        status, data = property_routes.list_properties(org_id, user, query)
        logger.info("GET /api/orgs/%s/properties -> %d", org_id, status)
        return "json", status, data

    # Properties: list by fund
    m = RE_FUND_PROPERTIES.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        fund_id = m.group(1)
        status, data = property_routes.list_by_fund(fund_id, user)
        logger.info("GET /api/funds/%s/properties -> %d", fund_id, status)
        return "json", status, data

    # Properties: get one
    m = RE_PROPERTY.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        property_id = m.group(1)
        status, data = property_routes.get_property(property_id, user)
        logger.info("GET /api/properties/%s -> %d", property_id, status)
        return "json", status, data

    # Fund-properties: list by org
    m = RE_ORG_FUND_PROPS.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id = m.group(1)
        status, data = fp_routes.list_by_org(org_id, user)
        logger.info("GET /api/orgs/%s/fund-properties -> %d", org_id, status)
        return "json", status, data

    # Fund-properties: list by fund
    m = RE_FUND_FUND_PROPS.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        fund_id = m.group(1)
        status, data = fp_routes.list_by_fund(fund_id, user)
        logger.info("GET /api/funds/%s/fund-properties -> %d", fund_id, status)
        return "json", status, data

    # Fund-properties: list by property
    m = RE_PROPERTY_FUND_PROPS.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        property_id = m.group(1)
        status, data = fp_routes.list_by_property(property_id, user)
        logger.info("GET /api/properties/%s/fund-properties -> %d", property_id, status)
        return "json", status, data

    # Fund-properties: get one
    m = RE_FUND_PROP.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        fp_id = m.group(1)
        status, data = fp_routes.get(fp_id, user)
        logger.info("GET /api/fund-properties/%s -> %d", fp_id, status)
        return "json", status, data

    logger.info("GET %s - not found", path)
    return "json", 404, {"detail": "Not found"}


# ---------------------------------------------------------------------------
# POST
# ---------------------------------------------------------------------------
def handle_post(handler):
    path = handler.path
    logger.info("POST %s", path)

    # Auth: register
    if path == "/api/auth/register":
        body = _read_body(handler)
        logger.info("Processing registration for email=%s", body.get("email"))
        status, data = auth_routes.register(body)
        logger.info("POST /api/auth/register -> %d", status)
        return "json", status, data

    # Auth: login
    if path == "/api/auth/login":
        body = _read_body(handler)
        logger.info("Processing login for email=%s", body.get("email"))
        status, data = auth_routes.login(body)
        logger.info("POST /api/auth/login -> %d", status)
        return "json", status, data

    # Orgs: create
    if path in ("/api/orgs", "/api/orgs/"):
        user, err = _auth_or_401(handler)
        if err:
            return err
        body = _read_body(handler)
        status, data = org_routes.create_org(body, user)
        logger.info("POST /api/orgs -> %d", status)
        return "json", status, data

    # Funds: create under org
    m = RE_ORG_FUNDS.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id = m.group(1)
        body = _read_body(handler)
        status, data = fund_routes.create(org_id, body, user)
        logger.info("POST /api/orgs/%s/funds -> %d", org_id, status)
        return "json", status, data

    # Properties: create under org
    m = RE_ORG_PROPERTIES.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id = m.group(1)
        body = _read_body(handler)
        status, data = property_routes.create(org_id, body, user)
        logger.info("POST /api/orgs/%s/properties -> %d", org_id, status)
        return "json", status, data

    # Fund-properties: create under org
    m = RE_ORG_FUND_PROPS.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id = m.group(1)
        body = _read_body(handler)
        status, data = fp_routes.create(org_id, body, user)
        logger.info("POST /api/orgs/%s/fund-properties -> %d", org_id, status)
        return "json", status, data

    # Org members: add user
    m = RE_ORG_MEMBERS.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id = m.group(1)
        body = _read_body(handler)
        status, data = org_routes.add_member(org_id, body, user)
        logger.info("POST /api/orgs/%s/members -> %d", org_id, status)
        return "json", status, data

    # Org members: reset password
    m = RE_ORG_MEMBER_RESET_PW.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id, member_id = m.group(1), m.group(2)
        body = _read_body(handler)
        status, data = org_routes.reset_member_password(org_id, member_id, body, user)
        logger.info("POST /api/orgs/%s/members/%s/reset-password -> %d", org_id, member_id, status)
        return "json", status, data

    logger.info("POST %s - not found", path)
    return "json", 404, {"detail": "Not found"}


# ---------------------------------------------------------------------------
# PUT
# ---------------------------------------------------------------------------
def handle_put(handler):
    path = handler.path
    logger.info("PUT %s", path)

    # Orgs: update
    m = RE_ORG.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id = m.group(1)
        body = _read_body(handler)
        status, data = org_routes.update_org(org_id, body, user)
        logger.info("PUT /api/orgs/%s -> %d", org_id, status)
        return "json", status, data

    # Funds: update
    m = RE_FUND.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        fund_id = m.group(1)
        body = _read_body(handler)
        status, data = fund_routes.update(fund_id, body, user)
        logger.info("PUT /api/funds/%s -> %d", fund_id, status)
        return "json", status, data

    # Properties: update
    m = RE_PROPERTY.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        property_id = m.group(1)
        body = _read_body(handler)
        status, data = property_routes.update(property_id, body, user)
        logger.info("PUT /api/properties/%s -> %d", property_id, status)
        return "json", status, data

    # Fund-properties: update
    m = RE_FUND_PROP.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        fp_id = m.group(1)
        body = _read_body(handler)
        status, data = fp_routes.update(fp_id, body, user)
        logger.info("PUT /api/fund-properties/%s -> %d", fp_id, status)
        return "json", status, data

    # Org members: edit
    m = RE_ORG_MEMBER.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id, member_id = m.group(1), m.group(2)
        body = _read_body(handler)
        status, data = org_routes.edit_member(org_id, member_id, body, user)
        logger.info("PUT /api/orgs/%s/members/%s -> %d", org_id, member_id, status)
        return "json", status, data

    logger.info("PUT %s - not found", path)
    return "json", 404, {"detail": "Not found"}


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def handle_delete(handler):
    path = handler.path
    logger.info("DELETE %s", path)

    # Orgs: delete
    m = RE_ORG.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        org_id = m.group(1)
        status, data = org_routes.delete_org(org_id, user)
        logger.info("DELETE /api/orgs/%s -> %d", org_id, status)
        return "json", status, data

    # Funds: delete
    m = RE_FUND.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        fund_id = m.group(1)
        status, data = fund_routes.delete(fund_id, user)
        logger.info("DELETE /api/funds/%s -> %d", fund_id, status)
        return "json", status, data

    # Properties: delete
    m = RE_PROPERTY.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        property_id = m.group(1)
        status, data = property_routes.delete(property_id, user)
        logger.info("DELETE /api/properties/%s -> %d", property_id, status)
        return "json", status, data

    # Fund-properties: delete
    m = RE_FUND_PROP.match(path)
    if m:
        user, err = _auth_or_401(handler)
        if err:
            return err
        fp_id = m.group(1)
        status, data = fp_routes.delete(fp_id, user)
        logger.info("DELETE /api/fund-properties/%s -> %d", fp_id, status)
        return "json", status, data

    logger.info("DELETE %s - not found", path)
    return "json", 404, {"detail": "Not found"}
