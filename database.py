import pymongo
from pymongo import  MongoClient

cluster = MongoClient("mongodb+srv://Eyusuf:cC2taMKbtKHDuxWW@cluster0.9ybil71.mongodb.net/")

db = cluster["monthly_reports"]
collection = db["expense_data"]


#insert period as a document inside our mongodb
def insert_period(period,incomes,expenses,comment):
    return collection.insert_one({"key":period,"incomes":incomes,"expenses":expenses,"comment":comment})

def fetch_all_periods():
    res = collection.find()
    return res

def get_period(period):

    if not isinstance(period, dict):
        period = {"key": period}

    return collection.find(period)