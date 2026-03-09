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

        docs = []
        doc_mappings =[]

        with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:

            reader = csv.DictReader(csvfile)

            for row in reader:
                doc = self.build_document(row)
                docs.append(doc)
                
                doc_mapping = self.build_fund_property(row)
                doc_mappings.append(doc_mapping)
                

        if docs:
            result = self.collection.insert_many(docs)
            print(f"{len(result.inserted_ids)} funds inserted")
            
        if doc_mappings:
            result = self.collectionname_mapping.insert_many(doc_mappings)
            print(f"{len(result.inserted_ids)} fund mappingss inserted")



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