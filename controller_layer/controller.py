from utils.config import UPLOADS_DIR, index_name, model
from Service_layer.data_handling import fetch_from_files
from Service_layer.service import process_and_index_data
import os
from utils.mysql_connect import logger
from Service_layer import service
from langchain_pinecone import PineconeVectorStore
from utils.embeddings_utils import SentenceTransformerEmbedding
from flask import jsonify

def upload_files(file):
    try:
       
       file_path = os.path.join(UPLOADS_DIR, file.filename)
       with open(file_path, "wb") as buffer:
            buffer.write(file.read())

    # Process and index the uploaded file
       data = fetch_from_files(file_path)
       process_and_index_data(data)

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise

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
            response = service.pinecone_index.query(
                top_k=50,  # Number of results per page
                vector=query_embedding,
                include_metadata=True,
                cursor=cursor  # Use cursor for pagination
            )
            
            # Extract matches from the response
            matches = response.get("matches", [])
            all_matches.extend(matches)
            
            # Check if there's a cursor for the next page
            cursor = response.get("next_cursor")
            
            # Break the loop if no more results or cursor is None
            if not cursor:
                break
        
        # Process the matches
        if not all_matches:
            return {"results": "No results found."}
        
        chunks = [match["metadata"]["text"] for match in all_matches]
        #text = "\n\n".join([f"{chunk}" for chunk in chunks ])
        
        #final_summary = service.summarize_large_text(query_text,text)
        return service.convert_to_natural_language(chunks, query_text)
    
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise

    
def delete_files(filename):
    try:
        # Create a custom embedding object
        embedding = SentenceTransformerEmbedding(model)
        
        # Initialize PineconeVectorStore
        docsearch = PineconeVectorStore(index_name=index_name, embedding=embedding)
        
        # Build the query to find all vectors associated with the file
        query_embedding = embedding.embed_query(f"File: {filename}")
        
        # Perform the query to get relevant vectors
        response = service.pinecone_index.query(
            vector=query_embedding,
            top_k=1000,  # Adjust based on the expected number of vectors to retrieve
            include_metadata=True
        )
        
        # Extract IDs of vectors to delete
        vectors_to_delete = [
            match["id"] for match in response.get("matches", [])
            if match.get("metadata", {}).get("source", "").startswith(f"File: {filename}")
        ]
        
        if not vectors_to_delete:
            return jsonify({"message": f"No data found for file {filename}."})

        # Delete vectors from Pinecone
        service.pinecone_index.delete(ids=vectors_to_delete)

        # Delete the file from the uploads directory
        file_path = os.path.join(UPLOADS_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise