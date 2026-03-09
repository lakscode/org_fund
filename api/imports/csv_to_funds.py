import csv
import sys
import os
from datetime import datetime, UTC
from pymongo import MongoClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import config


class FundCSVImporter:

    def __init__(self, mongo_uri, db_name, collection_name, org_id, collectionname_mapping):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.collectionname_mapping = self.db[collectionname_mapping]
        self.org_id = org_id

    def build_document(self, row):

        now = datetime.now(UTC)

        _doc = {
            "orgId": self.org_id,
            "externalIds": {},
            "fundCode": row.get("hMy").rstrip(),
            "sCode": row.get("sCode").rstrip(),
            "fundName": row.get("sName").rstrip(),
            "fundType": "core",
            "status": "active",
            "vintageYear": "",
            "baseCurrency": "USD",
            "managers": [],
            "settings":{},
            "metadata": {},
            "createdAt": now,
            "updatedAt": now
        }

        return _doc
    
    def build_fund_property(self, row):

        now = datetime.now(UTC)

        _doc = {
            "orgId": self.org_id,
            "externalIds": {},
            "fundCode": row.get("hMy").rstrip(),
            "hProperty": row.get("hProperty").rstrip(),
            "startDate": now,
            "endDate":None,
            "ownershipPct":"",
            "role": "primary",
            "createdAt": now,
            "updatedAt": now
        }

        return _doc
        

    def import_csv_fund(self, csv_path):

        inserted = 0
        updated = 0
        mapping_inserted = 0
        mapping_updated = 0

        with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:

            reader = csv.DictReader(csvfile)

            for row in reader:
                doc = self.build_document(row)
                now = doc.pop("createdAt")
                doc.pop("updatedAt")

                filter_key = {"orgId": self.org_id, "fundCode": doc["fundCode"]}
                result = self.collection.update_one(
                    filter_key,
                    {
                        "$set": {**doc, "updatedAt": now},
                        "$setOnInsert": {"createdAt": now},
                    },
                    upsert=True,
                )
                if result.upserted_id:
                    inserted += 1
                elif result.modified_count:
                    updated += 1

                doc_mapping = self.build_fund_property(row)
                map_now = doc_mapping.pop("createdAt")
                doc_mapping.pop("updatedAt")

                map_filter = {
                    "orgId": self.org_id,
                    "fundCode": doc_mapping["fundCode"],
                    "hProperty": doc_mapping["hProperty"],
                }
                result = self.collectionname_mapping.update_one(
                    map_filter,
                    {
                        "$set": {**doc_mapping, "updatedAt": map_now},
                        "$setOnInsert": {"createdAt": map_now},
                    },
                    upsert=True,
                )
                if result.upserted_id:
                    mapping_inserted += 1
                elif result.modified_count:
                    mapping_updated += 1

        print(f"Funds: {inserted} inserted, {updated} updated")
        print(f"Fund mappings: {mapping_inserted} inserted, {mapping_updated} updated")



def import_funds(org_id, csvname):
    csv_name = "../data/table_fund_data.csv"
    if csv_name:
        csv_name= csvname
    if org_id:
        importer = FundCSVImporter(
            mongo_uri=config.MONGO_URI,
            db_name=config.MONGO_DB,
            collection_name="funds",
            org_id=org_id,
            collectionname_mapping="fund_properties"
        )

        importer.import_csv_fund(csv_name)