import datetime
from flask import Flask, request, jsonify
import mysql.connector
from pymongo import MongoClient
import csv
from flask_cors import CORS

import queryMapper as q1



app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Allow up to 16MB
CORS(app)

# Local MySQL Connection
mysql_conn = mysql.connector.connect(
    host="localhost", 
    user="root", 
    password="Jesus&me2023!!", 
    database="chatdb_sql" 
)

# Local MongoDB Connection
mongo_client = MongoClient("mongodb://localhost:27017/")  
mongo_db = mongo_client["chatdb_nosql"]  


# Upload Dataset to MySQL
@app.route('/upload/mysql', methods=['POST'])
def upload_to_mysql():
    try:
        # Access the uploaded file
        file = request.files['file']
        table_name = request.form['table']

        # Decode the binary stream to text
        file_stream = file.stream.read().decode('utf-8')
        data = csv.reader(file_stream.splitlines())

        # Process the CSV data
        cursor = mysql_conn.cursor()
        columns = next(data)  # Get column headers

        # Wrap column names in backticks for MySQL
        column_definitions = ', '.join(f'`{col.strip()}` TEXT' for col in columns)
        create_table_query = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({column_definitions})"
        cursor.execute(create_table_query)

        # Insert rows into the table
        for row in data:
            values = ', '.join(f"'{v}'" for v in row)
            insert_query = f"INSERT INTO `{table_name}` VALUES ({values})"
            cursor.execute(insert_query)

        mysql_conn.commit()
        return jsonify({"message": "Data uploaded successfully to MySQL."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Upload Dataset to MongoDB
import json

@app.route('/upload/mongodb', methods=['POST'])
def upload_json_to_mongodb():
    try:
        file = request.files['file']
        collection_name = request.form['collection']

        # Load JSON file content
        file_data = json.load(file)  # Read and parse the JSON content
        if isinstance(file_data, list):  # Ensure it's a list of documents
            documents = file_data
        else:
            return jsonify({"error": "The uploaded JSON must be an array of objects."}), 400

        # Insert documents into MongoDB
        collection = mongo_db[collection_name]
        collection.insert_many(documents)

        return jsonify({"message": "JSON data uploaded successfully to MongoDB."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Execute Query in MySQL
@app.route('/query/mysql', methods=['POST'])
def execute_mysql_query():
    try:
        # Extract the query from the request
        query = request.json['query']
        print(f"Executing SQL query: {query}")  # Debug log

        # Execute the SQL query
        cursor = mysql_conn.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Serialize TIMESTAMP/DATETIME fields to string
        for row in results:
            for key, value in row.items():
                if isinstance(value, (datetime.datetime, datetime.date)):
                    row[key] = value.isoformat()  # Convert to ISO 8601 string

        print(f"Query results: {results}")  # Debug log
        return jsonify(results)  # Return the results as JSON
    except Exception as e:
        print(f"Error executing query: {e}")  # Log the error
        return jsonify({"error": str(e)}), 500


# Execute Query in MongoDB
from bson.json_util import dumps

@app.route('/query/mongodb', methods=['POST'])
def execute_mongodb_query():
    try:
        query = request.json['query']
        collection_name = query['collection']
        filter_query = query.get('filter', {})

        # Access the MongoDB collection
        collection = mongo_db[collection_name]
        results = collection.find(filter_query)

        # Serialize results with bson.json_util.dumps
        return jsonify({"data": json.loads(dumps(results))})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Fetch MySQL Metadata
@app.route('/metadata/mysql', methods=['GET'])
def get_mysql_metadata():
    try:
        cursor = mysql_conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        metadata = {}
        for table in tables:
            cursor.execute(f"DESCRIBE {table}")
            metadata[table] = [row[0] for row in cursor.fetchall()]
        return jsonify(metadata)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Fetch MongoDB Metadata
@app.route('/metadata/mongodb', methods=['GET'])
def get_mongodb_metadata():
    try:
        collections = mongo_db.list_collection_names()
        metadata = {}
        for collection in collections:
            sample_doc = mongo_db[collection].find_one()
            metadata[collection] = list(sample_doc.keys()) if sample_doc else []
        return jsonify(metadata)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

#Delete table from mySQL
@app.route('/delete/mysql', methods=['POST'])
def delete_mysql_table():
    try:
        table_name = request.json['table']

        # Check if the table exists
        cursor = mysql_conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        mysql_conn.commit()

        return jsonify({"message": f"Table `{table_name}` deleted successfully (if it existed)."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Delete collection from MongoDB
@app.route('/delete/mongodb', methods=['POST'])
def delete_mongodb_collection():
    try:
        collection_name = request.json['collection']

        # Check if the collection exists
        if collection_name in mongo_db.list_collection_names():
            mongo_db[collection_name].drop()
            return jsonify({"message": f"Collection `{collection_name}` deleted successfully."})
        else:
            return jsonify({"message": f"Collection `{collection_name}` does not exist."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Run the Flask App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
