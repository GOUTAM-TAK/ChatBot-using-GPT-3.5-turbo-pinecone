from utils.config import UPLOADS_DIR, index_name, model, logger,pinecone,spec,collection,name_space
from Service_layer.data_handling import DataHandler
from Service_layer.service import DataProcessor
import os
import traceback
from sklearn.cluster import KMeans
import numpy as np
data_service = DataProcessor()
data_handler = DataHandler()
class FileController:
    def __init__(self):
        self.pinecone_index = self.initialize_index()  # Initialize Pinecone index
        self.clear_mongo_data()

    def upload_files(self, file):
        try:
            file_path = os.path.join(UPLOADS_DIR, file.filename)

            if os.path.exists(file_path):
                return "Same file name already present in directory."

            # Save the file
            with open(file_path, "wb") as buffer:
                buffer.write(file.read())

            # Process and index the uploaded file
            data = data_handler.fetch_from_files(file_path)
            return data_service.process_and_index_data(data)
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return "Unsuccessful file upload!"

    def handle_query(self, query_text, sources=None):
        try:
          if not isinstance(query_text, str):
            raise ValueError("Query must be a string")
        
          query_embedding = data_service.embedding.embed_query(query_text)
        
          filter_criteria = None
          if sources:
            filter_criteria = {"source": {"$in": sources}}

          response = self.pinecone_index.query(
            top_k=9999,
            vector=query_embedding,
            include_metadata=True,
            namespace='task1',
            filter=filter_criteria
          )

          matches = response.get("matches", [])
          if not matches:
            return "No results found."
        
          chunks = [match["metadata"]["text"] for match in matches]
          responses = data_service.convert_to_natural_language(chunks, query_text)
          result = data_service.final_response(responses, query_text)
        
          return result
    
        except Exception as e:
          logger.error(f"Error in handle_query: {e}")
          return "Unsuccessful operation, try again"

    def delete_files(self, filename):
        try:
            if filename == '':
                return "Please provide a correct file name."
            # Delete the file from the uploads directory
            file_path = os.path.join(UPLOADS_DIR, filename)
            if not os.path.exists(file_path):
                return "Invalid file name, provide a correct file name."

            for ids in self.pinecone_index.list(prefix=f'{filename}#', namespace=name_space):
                self.pinecone_index.delete(ids=ids, namespace=name_space)

            # Delete the file from the uploads directory
            os.remove(file_path)
            return f"File {filename} deleted successfully."
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise

    def initialize_index(self):
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
            return pinecone.Index(index_name)
        except Exception as e:
            print(f"Error initializing Pinecone index: {e}")
            traceback.print_exc()  # Print stack trace for detailed error information

    def clear_mongo_data(self):
        try:
            # Delete all documents from the collection
            result = collection.delete_many({})
            print(f"Deleted {result.deleted_count} documents from the collection.")
        except Exception as e:
            logger.error(f"Error while clearing MongoDB data: {e}")
            raise

    def get_all_sources(self):
        try:
            # Initialize an empty set to store unique source names
            sources = set()

            # Fetch all IDs in the specified namespace
            ids_list = self.pinecone_index.list(namespace=name_space)

            if not ids_list:
                print("No sources available in the specified namespace.")
                return sources  # Returns an empty set

            for id_string in ids_list:
                if isinstance(id_string, list):
                    for single_id in id_string:
                        source = single_id.split('#')[0]
                        sources.add(source)
                else:
                    source = id_string.split('#')[0]
                    sources.add(source)
            return list(sources)
        except Exception as e:
            logger.error(f"Error in get_all_sources: {e}")
            raise
