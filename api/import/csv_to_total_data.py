import csv
import sys
import os
from pymongo import MongoClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import config


class CSVSelectedRows:

    def __init__(self, mongo_uri, db_name, collection):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection]

    def to_float(self, value):
        try:
            return float(str(value).replace(",", "").strip())
        except:
            return 0.0

    def process_csv(self, file_path, selected_rows, fundId, orgId, sCode):

        columns = [
            "hAccount",
            "sAccountCode",
            "sAccountName",
            "sBegin",
            "sMTD",
            "newTotal",
            "sAccountType"
        ]

        data = []

        totals = {
            "sBegin": 0,
            "sMTD": 0,
            "newTotal": 0
        }

        selected_rows = set(selected_rows)

        with open(file_path, newline='', encoding="utf-8-sig") as f:

            reader = csv.DictReader(f)

            for index, row in enumerate(reader, start=1):
                index = index +1
                print("\nindex", index)
                print("row ", row)
                if index not in selected_rows:
                    continue

                record = {}
                
                for col in columns:
                    record[col] = row.get(col)
                    print("col ", col, "record[col]   ", record[col] )

                begin = self.to_float(row.get("sBegin"))
                mtd = self.to_float(row.get("sMTD"))
                total = self.to_float(row.get("newTotal"))

                record["sBegin"] = begin
                record["sMTD"] = mtd
                record["newTotal"] = total
                record["row"] = index

                #totals["sBegin"] += begin
                #totals["sMTD"] += mtd
                #totals["newTotal"] += total

                data.append(record)

        document = {
            "fundId": fundId,
            "sCode": sCode,
            "orgId": orgId,
            #"totals": totals,
            "data": data
        }

        result = self.collection.update_one({"fundId": fundId}, {"$set":document}, upsert= True)

        
        
processor = CSVSelectedRows(
    config.MONGO_URI,
    config.MONGO_DB,
    "balance_sheet"
)

selected_rows = [27, 30, 38, 58, 100, 91, 123, 13, 105, 129, 69]

processor.process_csv(
    "../data/totals_data.csv",
    selected_rows,
    fundId="69a96f9182149d2a8b4f50bd",
    sCode="lt_2004",
    orgId="69a94fb12ef5155ff110c951"
)

