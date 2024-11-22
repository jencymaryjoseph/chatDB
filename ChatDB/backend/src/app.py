from flask import Flask, jsonify
import mysql.connector
from pymongo import MongoClient
from datetime import timedelta, datetime
import json

app = Flask(__name__)

# MySQL Connection
mysql_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jesus&me2023!!", 
    database="chatdb_sql"
)

# MongoDB Connection
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["chatdb_nosql"]

# Helper function to serialize objects that can't be JSON serialized
def serialize(obj):
    if isinstance(obj, timedelta):
        return str(obj) 
    elif isinstance(obj, datetime):
        return obj.isoformat() 
    else:
        return obj 

@app.route('/')
def home():
    return "ChatDB Backend running with Flask"

@app.route('/mysql-sales', methods=['GET'])
def get_mysql_sales():
    cursor = mysql_connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM coffee_sales LIMIT 10")
    results = cursor.fetchall()
    serialized_results = [{key: serialize(value) for key, value in row.items()} for row in results]
    cursor.close()
    return jsonify(serialized_results)

@app.route('/mongo-sales', methods=['GET'])
def get_mongo_sales():
    sales = mongo_db.coffee_sales.find().limit(10)
    sales_list = list(sales)
    for sale in sales_list:
        sale["_id"] = str(sale["_id"])  
    return jsonify(sales_list)

if __name__ == "__main__":
    app.run(debug=True, port=5005)
