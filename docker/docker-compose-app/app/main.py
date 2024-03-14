from pymongo import MongoClient
from pprint import pprint

# Connect to MongoDB
client = MongoClient('mongodb://mongo:27017/')
db = client.admin
dbs_list = db.command('listDatabases')
pprint(dbs_list)
print('MongoDB connected')