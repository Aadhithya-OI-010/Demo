from datetime import datetime
from pymongo import MongoClient
from pprint import pprint
import uuid


try:
 client = MongoClient("mongodb://localhost:27017/")
 print("Connected successfully")
except:
   print("Connection error")

db= client["Candidates"]
User= db["User"]
Issue= db["Issue"]

users=[
    {
        "uuid": str(uuid.uuid4()),
        "candidate":"John Doe",
        "email":"aadhihyasridhar06@gmail.com",
        "Scheduled_date":datetime(2026, 1, 29),
        "Interview_date": datetime( 2026, 2, 2)
    },
    {
        "uuid": str(uuid.uuid4()),
        "candidate":"Jenny Doe",
        "email":"aadhithya120906@gmail.com",
        "Scheduled_date":datetime(2026, 1, 30),
        "Interview_date":datetime( 2026, 2, 4)
    }
]
User.insert_many(users)

for doc in User.find():
  pprint(doc)

