"""
Seed script: imports all CSV files from api/data/ into MongoDB
using the existing schema (organizations, funds, properties, fund_properties,
tenants, units, sqft, totals, fund_transactions).

Usage:  python seed.py          (imports all)
        python seed.py --drop   (drops existing data first)
"""

import csv
import os
import sys
from datetime import datetime, timezone

from app.config import config
from app.database import (
    db,
    users_col,
    organizations_col,
    funds_col,
    properties_col,
    fund_properties_col,
    tenants_col,
    units_col,
    sqft_col,
    totals_col,
    fund_transactions_col,
)
from app.auth import hash_password
from app.logger import get_logger

logger = get_logger("seed")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

PROP_TYPE_MAP = {
    0: "other",
    1: "residential",
    2: "commercial",
    3: "industrial",
    4: "retail",
    5: "office",
    6: "mixed",
}

TENANT_STATUS_MAP = {
    0: "current",
    1: "past",
    2: "applicant",
    3: "future",
}


def _val(v):
    """Convert CSV value: NULL -> None, strip whitespace."""
    if v is None:
        return None
    v = v.strip()
    if v == "NULL" or v == "":
        return None
    return v


def _int(v):
    v = _val(v)
    if v is None:
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _float(v):
    v = _val(v)
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _bool(v):
    v = _val(v)
    if v is None:
        return False
    return v in ("1", "-1", "True", "true")


def _now():
    return datetime.now(timezone.utc)


def read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    logger.info("Reading CSV: %s", path)
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    logger.info("Read %d rows from %s", len(rows), filename)
    return rows


# ---- Default org (all data belongs to one org for now) ----
def ensure_default_org():
    org = organizations_col.find_one({"name": "Lotus Pacific"})
    if org:
        logger.info("Default org already exists: %s", org["_id"])
        return str(org["_id"])
    result = organizations_col.insert_one({
        "name": "Lotus Pacific",
        "status": "active",
        "createdAt": _now(),
        "updatedAt": _now(),
    })
    logger.info("Created default org: %s", result.inserted_id)
    return str(result.inserted_id)


# ---- Funds (table_fund_data.csv) ----
def import_funds(org_id):
    rows = read_csv("table_fund_data.csv")
    docs = []
    now = _now()
    for r in rows:
        level = _int(r.get("iLevel"))
        fund_type = "other"
        if level == 200:
            fund_type = "holding"
        elif level == 600:
            fund_type = "lp"
        elif level == 660:
            fund_type = "gp"
        elif level == 700:
            fund_type = "parent"

        docs.append({
            "orgId": org_id,
            "externalIds": [{"system": "legacy", "id": str(_int(r.get("hMy")))}],
            "fundCode": _val(r.get("sCode")) or "",
            "fundName": _val(r.get("sName")) or "",
            "fundType": fund_type,
            "vintageYear": None,
            "baseCurrency": "CAD",
            "status": "closed" if _bool(r.get("bInactive")) else "active",
            "managers": [],
            "settings": {
                "level": level,
                "totalInvestment": _float(r.get("dTotInvestment")),
                "minInvestment": _float(r.get("dMinInvestment")),
                "shares": _float(r.get("dShares")),
                "managementFee": _float(r.get("dManagementFee")),
                "objective": _val(r.get("sObjective")),
            },
            "address": {
                "line1": _val(r.get("sAddr1")) or "",
                "line2": _val(r.get("sAddr2")) or "",
                "city": _val(r.get("sCity")) or "",
                "state": _val(r.get("sState")) or "",
                "postalCode": _val(r.get("sZipCode")) or "",
            },
            "_legacyId": _int(r.get("hMy")),
            "_legacyPropertyId": _int(r.get("hProperty")),
            "createdAt": now,
            "updatedAt": now,
        })
    if docs:
        funds_col.insert_many(docs)
        logger.info("Imported %d funds", len(docs))
    fund_map = {d["_legacyId"]: d for d in docs}
    # Map legacy property id -> fund mongo _id (string)
    prop_to_fund = {}
    for d in docs:
        plid = d.get("_legacyPropertyId")
        if plid:
            prop_to_fund[plid] = str(d["_id"])
    return fund_map, prop_to_fund


# ---- Properties (table_property.csv) ----
def import_properties(org_id):
    rows = read_csv("table_property.csv")
    docs = []
    now = _now()
    for r in rows:
        itype = _int(r.get("ITYPE")) or 0
        prop_type = PROP_TYPE_MAP.get(itype, "other")
        inactive = _bool(r.get("bInactive"))

        docs.append({
            "orgId": org_id,
            "externalIds": [{"system": "legacy", "id": str(_int(r.get("HMY")))}],
            "propertyCode": (_val(r.get("SCODE")) or "").strip(),
            "propertyName": (_val(r.get("SADDR1")) or "").strip(),
            "address": {
                "line1": (_val(r.get("SADDR1")) or "").strip(),
                "line2": (_val(r.get("SADDR2")) or "").strip(),
                "city": (_val(r.get("SCITY")) or "").strip(),
                "state": (_val(r.get("SSTATE")) or "").strip(),
                "postalCode": (_val(r.get("SZIPCODE")) or "").strip(),
                "country": "CA",
            },
            "market": (_val(r.get("SCITY")) or "").strip(),
            "propertyType": prop_type,
            "status": "inactive" if inactive else "active",
            "acquisitionDate": _val(r.get("SACQUIRE")),
            "fundIds": [],
            "ownership": {
                "ownershipPct": 100,
                "consolidates": True,
            },
            "metadata": {
                "purchasePrice": _float(r.get("DPPRICE")),
                "endOfYear": _int(r.get("IENDOFYEAR")),
                "ncreif": _val(r.get("SNCREIF")),
                "legalEntityId": _int(r.get("hLegalEntity")),
            },
            "_legacyId": _int(r.get("HMY")),
            "createdAt": now,
            "updatedAt": now,
        })
    if docs:
        properties_col.insert_many(docs)
        logger.info("Imported %d properties", len(docs))
    return {d["_legacyId"]: d for d in docs}


# ---- Owners / Legal Entities (table_owner.csv) ----
def import_owners(org_id):
    """Import as supplementary owner data into a separate collection, and
       also link to organizations where applicable."""
    rows = read_csv("table_owner.csv")
    owners_col = db["owners"]
    docs = []
    now = _now()
    for r in rows:
        docs.append({
            "orgId": org_id,
            "externalIds": [{"system": "legacy", "id": str(_int(r.get("HMYPERSON")))}],
            "ownerCode": (_val(r.get("UCODE")) or "").strip(),
            "ownerName": (_val(r.get("ULASTNAME")) or "").strip(),
            "consolidate": _bool(r.get("BCONSOLIDATE")),
            "currency": _int(r.get("HCURRENCY")),
            "vatRegistered": _bool(r.get("iVatRegistered")),
            "regNum": _val(r.get("sRegNum")),
            "email": _val(r.get("sEmail2")),
            "international": _bool(r.get("bInternational")),
            "_legacyId": _int(r.get("HMYPERSON")),
            "createdAt": now,
            "updatedAt": now,
        })
    if docs:
        owners_col.drop()
        owners_col.insert_many(docs)
        owners_col.create_index("orgId")
        owners_col.create_index("_legacyId")
        logger.info("Imported %d owners", len(docs))
    return {d["_legacyId"]: d for d in docs}


# ---- Property-Owner links (table_propown.csv) → fund_properties ----
def import_prop_owner_links(org_id, prop_map, owner_map, prop_to_fund):
    rows = read_csv("table_propown.csv")
    docs = []
    for r in rows:
        prop_legacy = _int(r.get("HPROPERTY"))
        owner_legacy = _int(r.get("HOWNER"))
        pct = _float(r.get("DPERCENT"))

        prop = prop_map.get(prop_legacy)
        owner = owner_map.get(owner_legacy)
        if not prop or not owner:
            continue

        prop_id = None
        for p in properties_col.find({"_legacyId": prop_legacy, "orgId": org_id}):
            prop_id = str(p["_id"])
            break

        fund_id = prop_to_fund.get(prop_legacy)

        docs.append({
            "orgId": org_id,
            "fundId": fund_id,
            "propertyId": prop_id,
            "ownerLegacyId": owner_legacy,
            "startDate": _val(r.get("DINVESTDATE")),
            "endDate": None,
            "ownershipPct": pct,
            "role": "primary",
            "_legacyId": _int(r.get("HMY")),
        })
    if docs:
        fund_properties_col.insert_many(docs)
        logger.info("Imported %d property-owner links", len(docs))


# ---- Tenants (table_tenant.csv) ----
def import_tenants(org_id):
    rows = read_csv("table_tenant.csv")
    docs = []
    now = _now()
    for r in rows:
        status_code = _int(r.get("ISTATUS")) or 0
        docs.append({
            "orgId": org_id,
            "externalIds": [{"system": "legacy", "id": str(_int(r.get("HMYPERSON")))}],
            "tenantCode": (_val(r.get("SCODE")) or "").strip(),
            "lastName": (_val(r.get("SLASTNAME")) or "").strip(),
            "firstName": (_val(r.get("SFIRSTNAME")) or "").strip(),
            "propertyLegacyId": _int(r.get("HPROPERTY")),
            "unitCode": (_val(r.get("SUNITCODE")) or "").strip(),
            "status": TENANT_STATUS_MAP.get(status_code, "unknown"),
            "address": {
                "line1": (_val(r.get("SADDR1")) or "").strip(),
                "line2": (_val(r.get("SADDR2")) or "").strip(),
                "city": (_val(r.get("SCITY")) or "").strip(),
                "state": (_val(r.get("SSTATE")) or "").strip(),
                "postalCode": (_val(r.get("SZIPCODE")) or "").strip(),
            },
            "rent": _float(r.get("SRENT")),
            "leaseFrom": _val(r.get("DTLEASEFROM")),
            "leaseTo": _val(r.get("DTLEASETO")),
            "moveIn": _val(r.get("DTMOVEIN")),
            "moveOut": _val(r.get("DTMOVEOUT")),
            "commercial": _bool(r.get("BCOMMERCIAL")),
            "email": _val(r.get("SEMAIL")),
            "leaseCompany": (_val(r.get("SLEASECOMPANY")) or "").strip(),
            "leaseGrossSqft": _float(r.get("DLEASEGROSSSQFT")),
            "leaseNetSqft": _float(r.get("DLEASENETSQFT")),
            "unitLegacyId": _int(r.get("HUNIT")),
            "_legacyId": _int(r.get("HMYPERSON")),
            "createdAt": now,
            "updatedAt": now,
        })
    if docs:
        tenants_col.insert_many(docs)
        logger.info("Imported %d tenants", len(docs))


# ---- Units (table_unit.csv) ----
def import_units(org_id):
    rows = read_csv("table_unit.csv")
    docs = []
    now = _now()
    for r in rows:
        docs.append({
            "orgId": org_id,
            "externalIds": [{"system": "legacy", "id": str(_int(r.get("HMY")))}],
            "propertyLegacyId": _int(r.get("HPROPERTY")),
            "unitCode": (_val(r.get("SCODE")) or "").strip(),
            "rent": _float(r.get("SRENT")),
            "sqft": _float(r.get("DSQFT")),
            "rentalType": _int(r.get("IRENTALTYPE")),
            "bedrooms": _int(r.get("IBEDROOMS")),
            "excluded": _bool(r.get("EXCLUDE")),
            "type": _int(r.get("iType")),
            "_legacyId": _int(r.get("HMY")),
            "createdAt": now,
            "updatedAt": now,
        })
    if docs:
        units_col.insert_many(docs)
        logger.info("Imported %d units", len(docs))


# ---- Sqft (table_sqft.csv) ----
def import_sqft(org_id):
    rows = read_csv("table_sqft.csv")
    docs = []
    for r in rows:
        docs.append({
            "orgId": org_id,
            "type": _int(r.get("ITYPE")),
            "propertyLegacyId": _int(r.get("HPOINTER")),
            "date": _val(r.get("DTDATE")),
            "sqft": [_float(r.get(f"DSQFT{i}")) for i in range(16)],
            "notes": _val(r.get("sNotes")),
            "_legacyId": _int(r.get("HMY")),
        })
    if docs:
        sqft_col.insert_many(docs)
        logger.info("Imported %d sqft records", len(docs))


# ---- Totals / Financials (table_total.csv) ----
def import_totals(org_id):
    rows = read_csv("table_total.csv")
    docs = []
    for r in rows:
        docs.append({
            "orgId": org_id,
            "propertyLegacyId": _int(r.get("HPPTY")),
            "month": _val(r.get("UMONTH")),
            "book": _int(r.get("IBOOK")),
            "accountId": _int(r.get("HACCT")),
            "begin": _float(r.get("SBEGIN")),
            "mtd": _float(r.get("SMTD")),
            "beginBudget": _float(r.get("SBEGINBUDGET")),
            "budget": _float(r.get("SBUDGET")),
        })
    if docs:
        totals_col.insert_many(docs)
        logger.info("Imported %d total records", len(docs))


# ---- Fund Transactions (table_fund_tran.csv) ----
def import_fund_transactions(org_id):
    rows = read_csv("table_fund_tran.csv")
    docs = []
    now = _now()
    for r in rows:
        docs.append({
            "orgId": org_id,
            "externalIds": [{"system": "legacy", "id": str(_int(r.get("hMy")))}],
            "investorId": _int(r.get("hInvestor")),
            "investmentId": _int(r.get("hInvestment")),
            "category": (_val(r.get("sCategory")) or "").strip(),
            "amount": _float(r.get("dAmount")),
            "shares": _float(r.get("dShares")),
            "percent": _float(r.get("dPercent")),
            "totalAmount": _float(r.get("dTotAmount")),
            "totalShares": _float(r.get("dTotShares")),
            "totalPercent": _float(r.get("dTotPercent")),
            "isTotal": _bool(r.get("bTotal")),
            "startDate": _val(r.get("dtStart")),
            "endDate": _val(r.get("dtEnd")),
            "sharePrice": _float(r.get("dSharePrice")),
            "outstandingCommitment": _float(r.get("dOutstandingCommitment")),
            "notes": _val(r.get("sNotes")),
            "_legacyId": _int(r.get("hMy")),
            "createdAt": now,
            "updatedAt": now,
        })
    if docs:
        fund_transactions_col.insert_many(docs)
        logger.info("Imported %d fund transactions", len(docs))


# ---- Seed Users & Orgs ----
SEED_ORGS = [
    {"name": "Lotus Pacific", "status": "active"},
    {"name": "Maple Investments", "status": "active"},
    {"name": "Pacific Capital", "status": "active"},
]

SEED_USERS = [
    # (email, name, password, [(org_name, role)])
    ("admin@lotuspac.com", "Admin User", "password123", [
        ("Lotus Pacific", "admin"), ("Maple Investments", "admin"), ("Pacific Capital", "admin"),
    ]),
    ("john@lotuspac.com", "John Smith", "password123", [
        ("Lotus Pacific", "portfolio_manager"), ("Maple Investments", "analyst"),
    ]),
    ("sarah@maple.com", "Sarah Chen", "password123", [
        ("Maple Investments", "portfolio_manager"), ("Pacific Capital", "analyst"),
    ]),
    ("mike@pacific.com", "Mike Johnson", "password123", [
        ("Pacific Capital", "portfolio_manager"),
    ]),
]


def seed_orgs_and_users():
    """Create orgs and users, assign users to multiple orgs."""
    now = _now()
    org_name_to_id = {}

    # Create orgs
    for org_def in SEED_ORGS:
        existing = organizations_col.find_one({"name": org_def["name"]})
        if existing:
            org_name_to_id[org_def["name"]] = str(existing["_id"])
            logger.info("Org already exists: %s (%s)", org_def["name"], existing["_id"])
        else:
            result = organizations_col.insert_one({
                "name": org_def["name"],
                "status": org_def["status"],
                "createdAt": now,
                "updatedAt": now,
            })
            org_name_to_id[org_def["name"]] = str(result.inserted_id)
            logger.info("Created org: %s (%s)", org_def["name"], result.inserted_id)

    # Create super admin
    hashed = hash_password("password123")
    existing_sa = users_col.find_one({"email": "superadmin@restackai.com"})
    if not existing_sa:
        all_org_ids = list(org_name_to_id.values())
        all_org_roles = [{"org_id": oid, "role": "admin"} for oid in all_org_ids]
        result = users_col.insert_one({
            "email": "superadmin@restackai.com",
            "name": "Super Admin",
            "hashed_password": hashed,
            "org_ids": all_org_ids,
            "org_roles": all_org_roles,
            "isSuperAdmin": True,
        })
        logger.info("Created super admin: superadmin@restackai.com (%s)", result.inserted_id)
    else:
        logger.info("Super admin already exists: superadmin@restackai.com")

    # Create users
    for email, name, _pw, org_role_list in SEED_USERS:
        existing = users_col.find_one({"email": email})
        if existing:
            logger.info("User already exists: %s", email)
            continue
        org_roles = []
        org_id_strs = []
        for org_name, role in org_role_list:
            if org_name in org_name_to_id:
                oid = org_name_to_id[org_name]
                org_id_strs.append(oid)
                org_roles.append({"org_id": oid, "role": role})
        result = users_col.insert_one({
            "email": email,
            "name": name,
            "hashed_password": hashed,
            "org_ids": org_id_strs,
            "org_roles": org_roles,
        })
        logger.info("Created user: %s (%s) -> orgs: %s", email, result.inserted_id,
                     [n for n, _ in org_role_list])

    logger.info("Seeded %d orgs and %d users", len(SEED_ORGS), len(SEED_USERS))
    return org_name_to_id


# ---- Main ----
def drop_all():
    logger.info("Dropping all seeded collections")
    for col_name in ["users", "organizations", "funds", "properties", "fund_properties",
                     "tenants", "units", "sqft", "totals", "fund_transactions", "owners"]:
        db[col_name].delete_many({})
        logger.info("Cleared %s", col_name)


def seed():
    drop_flag = "--drop" in sys.argv
    if drop_flag:
        drop_all()

    org_name_to_id = seed_orgs_and_users()
    org_id = org_name_to_id["Lotus Pacific"]

    logger.info("=== Importing funds ===")
    fund_map, prop_to_fund = import_funds(org_id)

    logger.info("=== Importing properties ===")
    prop_map = import_properties(org_id)

    logger.info("=== Importing owners ===")
    owner_map = import_owners(org_id)

    logger.info("=== Importing property-owner links ===")
    import_prop_owner_links(org_id, prop_map, owner_map, prop_to_fund)

    logger.info("=== Importing tenants ===")
    import_tenants(org_id)

    logger.info("=== Importing units ===")
    import_units(org_id)

    logger.info("=== Importing sqft ===")
    import_sqft(org_id)

    logger.info("=== Importing totals ===")
    import_totals(org_id)

    logger.info("=== Importing fund transactions ===")
    import_fund_transactions(org_id)

    # Print summary
    logger.info("=== Seed complete ===")
    for col_name in ["organizations", "funds", "properties", "fund_properties",
                     "owners", "tenants", "units", "sqft", "totals", "fund_transactions"]:
        count = db[col_name].count_documents({})
        logger.info("  %s: %d documents", col_name, count)


if __name__ == "__main__":
    seed()
