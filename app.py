import os
import traceback
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from utils.config import UPLOADS_DIR, logger
from controller_layer.controller import upload_files, delete_files, handle_query, initialize_index,startup_prompt,clear_mongo_data
# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

# Query data
@app.route('/query', methods=['POST'])
def query_data():
    try:
        query_text = request.json.get('query')
        response = handle_query(query_text)
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
            return jsonify({"detail": "No file part in the request"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"detail": "No selected file"}), 400
        
        upload_files(file)

        return jsonify({"message": f"File {file.filename} uploaded successfully!"})
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({"error": "Error uploading file"}), 500
    

# List all files in the uploads directory
@app.route('/listfiles/', methods=['GET'])
def list_files():
    try:
        files = os.listdir(UPLOADS_DIR)
        return jsonify({"files": files})
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({"error": "Error listing files"}), 500

# Delete a file and its associated data in Pinecone
@app.route('/deletefile/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
       delete_files(filename)

       return jsonify({"message": f"File {filename} and its data deleted successfully."})
    
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({"error": "Error deleting file"}), 500
    
"""@app.teardown_appcontext
def cleanup(exception=None):
    # Ensure this only runs during the application teardown
    if exception:
        logger.error(f"Exception during request processing: {exception}")
    clear_mongo_data()
    logger.info("Application stopped and MongoDB data cleared.")"""

if __name__ == "__main__":
    try:
        clear_mongo_data()
        initialize_index()
        startup_prompt()
        app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
    except Exception as e:
        clear_mongo_data()
        print("Application stopped and MongoDB data cleared.")