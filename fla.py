import ollama
from flask import Flask, jsonify, request
from flask_cors import CORS
import re

app = Flask(__name__)
cors=CORS(app, resources={r"/": {"origins": ""}},supports_credentials=True) 
# Define functions to set and get schema within the application context
import mysql
host = 'localhost'
user = 'root'
password = 'Raj@2809'
database = 'sqlbuilder'

def connect_to_mysql_server(host, user, password, database):
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        print("Connected to MySQL Server")
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL Server: {e}")
        return None
connection=connect_to_mysql_server(host, user, password, database)
@app.route('/api/query', methods=['POST'])
def query():
    # Get query from request data
    data = request.get_json()
    query = data.get('query')
    result = execute_query(connection,query)

#     return jsonify(result)
def get_tables(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        return [table[0] for table in tables]  #
    except mysql.connector.Error as e:
        print(f"Error retrieving tables: {e}")
        return []
    

def create_table(connection, tables,schema):
    try:
        cursor = connection.cursor()
        print(schema)
        cursor.execute(schema)
        print(f"Table created successfully")
        connection.commit()
    except mysql.connector.Error as e:
        print(f"Error creating table: {e}")
    

def find_empty_tables(connection):
    empty_tables = []
    cursor=connection.cursor()
    tables=cursor.execute("SHOW TABLES")
    # Loop through your tables and check for empty records
    for table in tables:   # Add more tables as needed
        count = table.query.count()
        if count == 0:
            empty_tables.append(table._tablename_)

    return empty_tables
def get_table_columns(connection, table_name):
    cursor = connection.cursor()
    cursor.execute(f"DESC {table_name}")
    columns = [row[0] for row in cursor.fetchall()]
    return columns

def set_schema(schema):
    schema = str(schema) + "\n your goal is to provide SQL query for the task given in the prompt."

def get_schema():
    return schema

def get_completion(schema, prompt):
    message = [
        {
            'role': 'system',
            'content': schema,
        },
        {
            'role': 'user',
            'content': prompt
        }
    ]
    response = ollama.chat(model='codeqwen', messages=message, stream=False)
    # response = {'message': {'content': 'hi'}}
    # response.headers.add('Access-Control-Allow-Origin', 'http://127.0.0.1:5500')
    extract_sql_string(response['message']['content'])
    return response['message']['content']

# Define Flask routes within the application context
import re


def extract_sql_string(content):
    # If content starts with SELECT, return the entire content
    if content.strip().lower().startswith('select'):
        execute_query(connection, content)
        return content.strip()
    
    # Extract SQL string using triple backticks ()
    sql_match = re.search(r'sql\s*(.?)\s', content, re.DOTALL)
    if sql_match:
        execute_query(connection, sql_match.group(1))
        return sql_match.group(1)
    
#     return None
def execute_query(connection, query):
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        results=cursor.fetchall()
        print(results)
        connection.commit()
        print("Query executed successfully")
        return results
    except:
        print("Error executing query")
        return None
        
# Example usage:
response_content = "Some text before\nsql\nSELECT * FROM table;\n``` Some text after"
sql_string = extract_sql_string(response_content)
if sql_string:
    print("SQL String:", sql_string)
else:
    print("No SQL string found in the response content.")

@app.route('/add-schema', methods=['POST'])
def add_schema_api():
    global schema
    schema = request.json['schema']
    set_schema(schema)
    tables=get_tables(connection)
    # print(schema)
    # create_table(connection,tables,schema)
    # print("Successfully created a new table")
    # insert_dummy_data(connection,)
    return jsonify({"message": "Schema added successfully"})
@app.route('/get-results',methods=['GET'])
def get_results(connection,query):
    cursor = connection.cursor()
    execute_query(connection,query)
    results=cursor.fetchall()
    print(results)
    return jsonify({"results":results})

@app.route('/get-completion', methods=['POST'])
def get_completion_api():
    prompt = request.json['prompt']
    schema = get_schema()
    if schema is None:
        return jsonify({"error": "Schema not found"})
    completion = get_completion(schema, prompt)
    return jsonify({"completion": completion})

if __name__ == '__main__':
    app.run(port=3000, debug=True)