from generator import *
from datetime import datetime
from pymongo import MongoClient

json_data = Json_fake(10).data
pd_data = CSV_fake(10).df

db_name = 'transactions'
collection_name = 'invoices'
uri = "mongodb://root:example@localhost:27017/"

client = MongoClient(uri)
db = client[db_name]
collection = db[collection_name]
collection.insert_many(json_data)
