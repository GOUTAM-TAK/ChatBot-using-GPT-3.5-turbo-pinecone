from utils.config import index_name, model, llm, UPLOADS_DIR,pinecone
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from utils.embeddings_utils import SentenceTransformerEmbedding
from datetime import datetime,date,time
from typing import List
from utils.config import logger
from utils.util_methods import store_query_response,fetch_recent_query_response

# Define custom JSON serializer for objects not serializable by default JSON encoder
def json_serialize(obj):
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

#process data and store into vector database
def process_and_index_data(data):
    try:
        if not data:
            logger.warning("No data to index.")
            return
        
        chunk_size = 500  # Define your chunk size
        batch_size = 40930  # Define batch size for upsert
        vectors = []

        for d in data:
            if isinstance(d, dict) and "data" in d:
                data_string = json.dumps(d["data"], default=json_serialize)
                source = d.get("source", "unknown")
            else:
                data_string = str(d)  # Handle cases where d might be a string directly
                source = "unknown"  # Default source for string data

            
            index = pinecone.Index(index_name)
            # Create a custom embedding object
            embedding = SentenceTransformerEmbedding(model)
             # Split data_string into chunks
            chunks = [data_string[i:i+chunk_size] for i in range(0, len(data_string), chunk_size)]

            # Process each chunk
            for i, chunk in enumerate(chunks):
                metadata = {"source": source, "chunk_id": i, "text":chunk}
                
                embeddings = embedding.embed_documents(chunk)

                vectors.append({
                    "id": f"{source}#{i}",
                    "values": embeddings,
                    "metadata": metadata
                })

                # Check if batch size is reached
                if len(vectors) <= batch_size:
                    # Upsert batch to Pinecone
                    index.upsert(
                        vectors=vectors,
                        namespace='task1'
                    )
                    print(f"Batch of {batch_size} indexed successfully.")
                    vectors = [] 
          # Upsert any remaining vectors
        if vectors:
            index.upsert(
                vectors=vectors,
                namespace='task1'
            )
            print(f"Final batch of {len(vectors)} indexed successfully.")

        print("Data indexed successfully in Pinecone.")
        return "file upload successfully!"
    except Exception as e:
        logger.error(f"Error processing and indexing data: {e}")
        raise

# Convert query results and user queries into natural language responses
def convert_to_natural_language(data: List[str], natural_language_text: str) -> str:
    try:
        if not data:
            return "No data present in the database for the given prompt. Please provide correct data."

        recent_query, recent_response = fetch_recent_query_response()
        
        prompt_template = """
        You are a helpful assistant that converts database query results into concise and precise natural language responses.

        Here is the natural language request:
        {natural_language_text}

        Here are the most recent previous user query and its response:
        Previous Query: {recent_query}
        Previous Response: {recent_response}

        Here are the query results:
        {data}

        Instructions:
        - Review the query results and determine if they are relevant to the given prompt.
        - If the data is relevant, generate a direct and precise natural language response based only on the provided results.
        - Also, review the Previous Query and Previous Response, and if they are helpful, use their information in the final response; otherwise, avoid these.
        - If the data is not relevant or if no relevant data is found, respond with: "No information available, please provide a correct prompt."
        - Do not add any additional information, explanations, or context.
        - Do not start the response with phrases like "Based on the provided query results" or similar.
        - Generate the response in a single sentence format.

        Please provide a response in natural language in a single sentence format based on these instructions.
        """

        prompt = PromptTemplate(input_variables=["natural_language_text", "recent_query", "recent_response", "data"], template=prompt_template)
        response_chain = LLMChain(prompt=prompt, llm=llm)

        formatted_data = "\n\n".join([f"Data:\n{data_item}" for data_item in data])

        result = response_chain.run(natural_language_text=natural_language_text, recent_query=recent_query, recent_response=recent_response, data=formatted_data)
        #store query and result into mongodb
        store_query_response(natural_language_text,result)

        return result.strip()
    except Exception as e:
        logger.error(f"Unexpected error in generating natural response: {e}")
        raise
    
def fetch_query_vector(query):
    try:
        query_vector = model.encode([query])
        return query_vector[0]
    except Exception as e:
        logger.error(f"Error encoding query: {e}")
        raise
