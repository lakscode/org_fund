import os
import re
import tempfile

from app.logger import get_logger

logger = get_logger("routes.imports")

# Lazy-import the importer functions so the module path works
_importers_loaded = False
_import_funds = None
_import_properties = None
_import_balance_sheet = None


def _load_importers():
    global _importers_loaded, _import_funds, _import_properties, _import_balance_sheet
    if _importers_loaded:
        return

    from imports.csv_to_funds import import_funds
    from imports.csv_to_properties import import_properties
    from imports.csv_to_total_data import import_balance_sheet
    _import_funds = import_funds
    _import_properties = import_properties
    _import_balance_sheet = import_balance_sheet
    _importers_loaded = True


def _parse_multipart(handler):
    """Parse multipart/form-data manually (no cgi.FieldStorage)."""
    content_type = handler.headers.get("Content-Type", "")
    if "multipart/form-data" not in content_type:
        return None, None

    # Extract boundary
    m = re.search(r"boundary=(.+)", content_type)
    if not m:
        return None, None
    boundary = m.group(1).strip().encode("utf-8")

    content_length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(content_length)

    fields = {}
    file_data = None
    file_name = None

    # Split on boundary
    parts = body.split(b"--" + boundary)
    for part in parts:
        part = part.strip()
        if not part or part == b"--":
            continue

        # Split headers from body at \r\n\r\n
        sep = part.find(b"\r\n\r\n")
        if sep < 0:
            continue
        header_block = part[:sep].decode("utf-8", errors="replace")
        part_body = part[sep + 4:]

        # Strip trailing \r\n
        if part_body.endswith(b"\r\n"):
            part_body = part_body[:-2]

        # Parse Content-Disposition
        cd_match = re.search(r'name="([^"]+)"', header_block)
        if not cd_match:
            continue
        name = cd_match.group(1)

        fn_match = re.search(r'filename="([^"]*)"', header_block)
        if fn_match:
            file_name = fn_match.group(1)
            file_data = part_body
        else:
            fields[name] = part_body.decode("utf-8", errors="replace")

    return fields, (file_name, file_data) if file_data is not None else None


def _save_temp_csv(file_tuple):
    """Save uploaded file bytes to a temp CSV and return the path."""
    _file_name, file_bytes = file_tuple
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "wb") as f:
        f.write(file_bytes)
    return path


def handle_import(handler, current_user):
    """Handle POST /api/import  (multipart/form-data)."""
    _load_importers()
    print("IN handle_import")
    fields, file_item = _parse_multipart(handler)
    if fields is None:
        return 400, {"detail": "Expected multipart/form-data"}

    import_type = fields.get("type", "")
    org_id = fields.get("orgId", "")

    if not import_type:
        return 400, {"detail": "Missing 'type' field (funds, properties, balancesheet)"}
    if not org_id:
        return 400, {"detail": "Missing 'orgId' field"}
    if not file_item:
        return 400, {"detail": "Missing CSV file"}

    # Check user belongs to this org
    user_orgs = current_user.get("org_ids", [])
    if org_id not in user_orgs:
        return 403, {"detail": "Not a member of this organization"}

    # Check admin role
    org_roles = current_user.get("org_roles", [])
    user_role = "member"
    for r in org_roles:
        if r.get("org_id") == org_id:
            user_role = r.get("role", "member")
            break
    if user_role != "admin":
        return 403, {"detail": "Only admins can import data"}

    csv_path = _save_temp_csv(file_item)
    logger.info("Import type=%s orgId=%s file=%s", import_type, org_id, csv_path)

    try:
        if import_type == "funds":
            _import_funds(org_id, csv_path)
            return 200, {"detail": "Funds imported successfully"}

        elif import_type == "properties":
            _import_properties(org_id, csv_path)
            return 200, {"detail": "Properties imported successfully"}

        elif import_type == "balancesheet":
            fund_id = fields.get("fundId", "")
            s_code = fields.get("sCode", "")
            if not fund_id:
                return 400, {"detail": "Missing 'fundId' for balance sheet import"}
            if not s_code:
                return 400, {"detail": "Missing 'sCode' for balance sheet import"}
            _import_balance_sheet(org_id, fund_id, s_code, csv_path)
            return 200, {"detail": "Balance sheet imported successfully"}

        else:
            return 400, {"detail": f"Unknown import type: {import_type}. Use funds, properties, or balancesheet"}

    except Exception as e:
        logger.error("Import failed: %s", e, exc_info=True)
        return 500, {"detail": f"Import failed: {str(e)}"}
    finally:
        try:
            os.unlink(csv_path)
        except OSError:
            pass
