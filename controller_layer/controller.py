from utils.config import UPLOADS_DIR, index_name, model, logger,pinecone,spec,collection,name_space
from Service_layer.data_handling import fetch_from_files
from Service_layer.service import process_and_index_data
import os
import traceback
from Service_layer import service
from utils.embeddings_utils import SentenceTransformerEmbedding
from flask import jsonify

def upload_files(file):
    try:
       
       file_path = os.path.join(UPLOADS_DIR, file.filename)

       if os.path.exists(file_path):
            return "Same file name already present in directory."
       
       with open(file_path, "wb") as buffer:
            buffer.write(file.read())

    # Process and index the uploaded file
       data = fetch_from_files(file_path)
       print("this is raw data extract from file",data)
       return process_and_index_data(data)
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return "unsuccessfull file upload!!"

def handle_query(query_text):
    try:
        # Ensure query_text is a string
        if not isinstance(query_text, str):
            raise ValueError("Query must be a string")
        
        # Create a custom embedding object
        embedding = SentenceTransformerEmbedding(model)
        
        # Embed the query text
        query_embedding = embedding.embed_query(query_text)
        
        all_matches = []
        cursor = None
        
        # Fetch results with pagination
        while True:
            response = pinecone_index.query(
                top_k=9999,  # Number of results per page
                vector=query_embedding,
                include_metadata=True,
                namespace='task1',
                cursor=cursor  # Use cursor for pagination
            )
            
            # Extract matches from the response
            matches = response.get("matches", [])
            all_matches.extend(matches)
            
            # Check if there's a cursor for the next page
            cursor = response.get("next_cursor")
            
            # Break the loop if no more results or cursor is None
            if cursor is None or len(matches) < 9999:
                break
        
        # Process the matches
        if not all_matches:
            return {"results": "No results found."}
        
        chunks = [match["metadata"]["text"] for match in all_matches]
        
        return service.convert_to_natural_language(chunks, query_text)
    
    except Exception as e:
        logger.error(f"error in handle query : {e}")
        return {"error": str(e)}

  
def delete_files(filename):
    try:
        if filename == '':
            return "please give correct file name"
        # Delete the file from the uploads directory
        file_path = os.path.join(UPLOADS_DIR, filename)
        if not os.path.exists(file_path):
            return "Invalid file name, give correct file name. "
        
        for ids in pinecone_index.list(prefix=f'{filename}#', namespace=name_space):
          print(ids) # ['doc1#chunk1', 'doc1#chunk2', 'doc1#chunk3']
          pinecone_index.delete(ids=ids, namespace=name_space)
        
        # Delete the file from the uploads directory
        os.remove(file_path)
        return f"File {filename} deleted successfully."
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise

def initialize_index():
    try:
        # Check if the index already exists
        if index_name not in pinecone.list_indexes().names():

            # Create the index with the specified parameters
            pinecone.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=spec
            )
            print("Index created successfully.")
        global pinecone_index
        pinecone_index = pinecone.Index(index_name)
        print(pinecone_index.describe_index_stats())
    except Exception as e:
        print(f"Error initializing Pinecone index: {e}")
        traceback.print_exc()  # Print stack trace for detailed error information
        

def clear_mongo_data():
    try:
        # Delete all documents from the collection
        result = collection.delete_many({})
        print(f"Deleted {result.deleted_count} documents from the collection.")
        
    except Exception as e:
        logger.error(f"Error while clearing MongoDB data: {e}")
        raise

def get_all_sources():
    try:
    # Initialize an empty set to store unique source names
      sources = set()
    
    # Iterate through all the IDs in the specified namespace
      # Fetch all IDs in the specified namespace
      ids_list = pinecone_index.list(namespace=name_space)
    
    # Check if any IDs are available
      if not ids_list:
        print("No sources available in the specified namespace.")
        return sources  # Returns an empty set

    # Iterate through each ID in the list
      for id_string in ids_list:
        # Check if id_string is a list of IDs
        if isinstance(id_string, list):
            # Flatten the list if necessary
            for single_id in id_string:
                # Split the ID at the '#' symbol and take the first part (prefix)
                source = single_id.split('#')[0]
                # Add the prefix to the set (duplicates will automatically be handled)
                sources.add(source)
        else:
            # Handle case where id_string is a single string
            source = id_string.split('#')[0]
            sources.add(source)
      return list(sources)
    except Exception as e:
        logger.error(f"error in get_all_source : {e}")
        raise
