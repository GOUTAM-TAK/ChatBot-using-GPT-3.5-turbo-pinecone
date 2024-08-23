import os
import re
import traceback
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from utils.config import UPLOADS_DIR, logger
from controller_layer.controller import FileController
# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = Flask(__name__, static_folder='static', template_folder='templates')
controller = FileController()

@app.route('/')
def index():
    return render_template('index.html')

# Query data
@app.route('/query', methods=['POST'])
def query_data():
    try:
        query_text = request.json.get('query')
         # Strip leading and trailing spaces from query_text
        query_text = query_text.strip()
        if query_text == '' :
          return {"response" : "query should be in correct form"}
         # Define a regex pattern to match special characters
        special_char_pattern = re.compile(r'[!@#%^&*()":{}|<>]')

        # Check if the query_text contains any special characters
        if special_char_pattern.search(query_text):
          return {"response": "Query should not contain special characters"}
        sources = request.json.get('sources')
         # Check if sources is empty or not provided
        if not sources:  # This checks if sources is None or an empty list
          return {"response": "sources list should not be empty"}
        
        response = controller.handle_query(query_text, sources=sources)
        return {"response": response}
    
    except Exception as e:
        logger.error(f"Error querying data: {e}")
        traceback.print_exc()  # Print stack trace for detailed error information
        return jsonify({"error": "Error querying data"}), 500

# Upload file
@app.route('/uploadfile/', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"message": "No file part in the request"})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"message": "No selected file"})
        
        return jsonify({"message": controller.upload_files(file)})
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({"message": "Error uploading file"}), 500
    

# List all files in the uploads directory
@app.route('/listfiles/', methods=['GET'])
def list_files():
    try:
        files = os.listdir(UPLOADS_DIR)
        return jsonify({"files": files})
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({"error": "Error listing files"}), 500

# List all sources in the pinecone
@app.route('/listsources/', methods=['GET'])
def list_sources():
    try:
        sources = controller.get_all_sources()
    
        # If sources is a list, return it as a JSON response
        if isinstance(sources, list):
          sources_sorted = sorted(sources)
          return jsonify({"sourcesList": sources_sorted})
    
        # If no sources are available, return a message
        return jsonify({"message": sources})
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({"error": "Error listing files"}), 500


# Delete a file and its associated data in Pinecone
@app.route('/deletefile/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
       
       return jsonify({"message": controller.delete_files(filename)}), 200
    
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({"error": "Error deleting file"}), 500

if __name__ == "__main__":    
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False, threaded = True)
