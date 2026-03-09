import csv
import sys
import os
from datetime import datetime, UTC
from pymongo import MongoClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import config


class PropertyCSVImporter:

    def __init__(self, mongo_uri, db_name, collection_name, org_id):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.org_id = org_id

    def build_property_document(self, row):

        now = datetime.now(UTC)

        property_doc = {
            "orgId": self.org_id,

            "externalIds": {},
            "propertyCode": row.get("HMY").rstrip(),
            "propertyName": row.get("SADDR1").rstrip(),
            "address": {
                "line1": row.get("SADDR2").rstrip(),
                "line2": None,
                "city": row.get("SCITY").rstrip(),
                "state": row.get("SSTATE").rstrip(),
                "postalCode": row.get("SZIPCODE").rstrip(),
                "country": "US"
            },
            "market": row.get("SCITY").rstrip(),
            "propertyType": row.get("ITYPE").rstrip(),
            "status": "active",
            "acquisitionDate": None,
            "ownership": {
                "ownershipPct": None,
                "consolidates": False
            },

            "metadata": {},

            "createdAt": now,
            "updatedAt": now
        }

        return property_doc


    def import_csv_property(self, csv_path):

        docs = []

        with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:

            reader = csv.DictReader(csvfile)

            for row in reader:
                doc = self.build_property_document(row)
                docs.append(doc)

        if docs:
            result = self.collection.insert_many(docs)
            print(f"{len(result.inserted_ids)} properties inserted")


def import_properties(org_id, csvname):
    csv_name = "../data/table_property.csv"
    if csvname:
        csv_name = csvname
    if org_id:
        importer = PropertyCSVImporter(
            mongo_uri=config.MONGO_URI,
            db_name=config.MONGO_DB,
            collection_name="properties",
            org_id=org_id
        )

        importer.import_csv_property(csv_name)