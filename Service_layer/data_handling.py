from utils.mysql_connect import connect_to_mysql, logger
import pandas as pd
from flask import jsonify
import os
import pdfplumber
def fetch_all_tables_data():
    try:
        connection = connect_to_mysql()
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        all_data = [] 

        for table in tables:
            table_name=table[0]
            query=f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, connection)
          
            for index, row in df.iterrows():
                row_data = row.to_dict()
                all_data.append({"data": row_data, "source":f"MySQL table : {table_name}"})

        cursor.close
        print("successfully fetch data from mysql database")
        connection.close()
        return all_data
    except Exception as e:
        logger.error(f"Error fetching data from MySQL: {e}")
        return jsonify({"detail":"Error fetching data from database"}),500
    
def extract_text_from_pdf(file_path):
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error reading PDF file {file_path}: {e}")
        raise

def fetch_from_files(file_path):
    try:
        data = []
         # Normalize path
        file_path = os.path.abspath(file_path)

        if os.path.isfile(file_path):
            #process single file
            if file_path.lower().endswith('.pdf'):
                # Read PDF file
                content = extract_text_from_pdf(file_path)
                data.append({"data": content, "source": f"File: {os.path.basename(file_path)}"})
            else:
              with open(file_path,'r') as file:
                 content = file.read()
                 data.append({"data": content, "source": f"File: {os.path.basename(file_path)}"})

        elif os.path.isdir(file_path):
            #process ALL files in a directory
            files = os.listdir(file_path)
            for file_name in files:
                full_file_path = os.path.join(file_path, file_name)
                if os.path.isfile(full_file_path):
                    if full_file_path.lower().endswith('.pdf'):
                        # Read PDF file
                        content = extract_text_from_pdf(full_file_path)
                    else:

                      with open(full_file_path,'r') as file:
                        content = file.read()
                        data.append({"data": content, "source": f"File: {file_name}"})
                        
        print("successfully fetch data from file")
        return data
    except Exception as e:
        logger.error(f"Error reading files from {file_path}: {e}")
        return jsonify({"detail":"Error in reading files"}),500
    



