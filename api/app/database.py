from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
from app.config import config
from app.logger import get_logger

logger = get_logger("database")

#logger.info("Connecting to MongoDB at %s, database: %s", config.MONGO_URI, config.MONGO_DB)
try:
    client = MongoClient(config.MONGO_URI)
    client.admin.command("ping")
    logger.info("MongoDB connection established successfully")
except ConnectionFailure as e:
    logger.error("Failed to connect to MongoDB: %s", e)
    raise

db = client[config.MONGO_DB]

# Collections
users_col = db["users"]
organizations_col = db["organizations"]
funds_col = db["funds"]
properties_col = db["properties"]
fund_properties_col = db["fund_properties"]
tenants_col = db["tenants"]
units_col = db["units"]
sqft_col = db["sqft"]
totals_col = db["totals"]
fund_transactions_col = db["fund_transactions"]
balance_sheet_col = db["balance_sheet"]

# Indexes
logger.info("Creating indexes")

users_col.create_index("email", unique=True)

organizations_col.create_index("name", unique=True)
organizations_col.create_index("status")

funds_col.create_index("orgId")
funds_col.create_index("fundCode")
funds_col.create_index([("orgId", ASCENDING), ("fundCode", ASCENDING)], unique=True)
funds_col.create_index("status")
funds_col.create_index("externalIds.system")

properties_col.create_index("orgId")
properties_col.create_index("propertyCode")
properties_col.create_index([("orgId", ASCENDING), ("propertyCode", ASCENDING)], unique=True)
properties_col.create_index("fundIds")
properties_col.create_index("status")
properties_col.create_index("market")
properties_col.create_index("propertyType")
properties_col.create_index("externalIds.system")

fund_properties_col.create_index("orgId")
fund_properties_col.create_index("fundId")
fund_properties_col.create_index("propertyId")
fund_properties_col.create_index([("fundId", ASCENDING), ("propertyId", ASCENDING)])

tenants_col.create_index("orgId")
tenants_col.create_index("propertyId")
tenants_col.create_index("unitCode")
tenants_col.create_index("status")

units_col.create_index("orgId")
units_col.create_index("propertyId")
units_col.create_index("unitCode")

sqft_col.create_index("propertyId")
sqft_col.create_index("type")

totals_col.create_index("propertyId")
totals_col.create_index("month")

fund_transactions_col.create_index("orgId")
fund_transactions_col.create_index("investorId")
fund_transactions_col.create_index("investmentId")
fund_transactions_col.create_index("category")

logger.info("Database initialization complete")


def get_db():
    return db
