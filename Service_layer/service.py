from Service_layer.data_handling import fetch_all_tables_data, fetch_from_files
from utils.mysql_connect import logger
from flask import jsonify
from utils.config import index_name, model, pinecone, llm, UPLOADS_DIR,spec
import traceback
from langchain_pinecone import PineconeVectorStore
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from utils.embeddings_utils import SentenceTransformerEmbedding
from datetime import datetime,date
from typing import List
from utils.utils_method import chunk_text,summarize_text
from utils.config import tokenizer
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
        return jsonify({"error":"Error Initializing pinecone index"}),500

# Define custom JSON serializer for objects not serializable by default JSON encoder
def json_serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

#process data and store into vector database
def process_and_index_data(data):
    try:
        if not data:
            logger.warning("No data to index.")
            return
        
        chunk_size = 1000  # Define your chunk size
        documents = []
        metadata_list = []

        for d in data:
            if isinstance(d, dict) and "data" in d:
                data_string = json.dumps(d["data"], default=json_serialize)
                source = d.get("source", "unknown")
            else:
                data_string = str(d)  # Handle cases where d might be a string directly
                source = "unknown"  # Default source for string data

            chunks = [data_string[i:i+chunk_size] for i in range(0, len(data_string), chunk_size)]
            for chunk in chunks:
                documents.append(chunk)
                metadata_list.append({"source": source})

        # Create a custom embedding object
        embedding = SentenceTransformerEmbedding(model)

        # Create or update the vector store
        docsearch = PineconeVectorStore.from_texts(
            texts=documents,
            embedding=embedding,  # Pass the embedding object
            metadatas=metadata_list,
            index_name=index_name
        )
        print("Data indexed successfully in Pinecone.")

    except Exception as e:
        logger.error(f"Error processing and indexing data: {e}")
        raise
    

# Convert query results and user queries into natural language responses
def convert_to_natural_language(data: List[str], natural_language_text: str) -> str:
    try:
        if not data:
            return "No data present in the database for the given prompt. Please provide correct data."

        prompt_template = """
        You are a helpful assistant that converts database query results into natural language responses.
        Here is the natural language request:
        {natural_language_text}

        Here are the query results:
        {data}

        Instructions:
        - Review the query results and determine if they are relevant to the given prompt.
        - If the data is relevant, generate a coherent natural language response based on only the provided results.
        - If the data is not relevant or if no relevant data is found, respond with: "No information available, please provide a correct prompt."
        - Not add any additional information in response.
        
        Please provide a response in natural language in paragraph format based on these instructions.
        """

        # Define the prompt template
        prompt = PromptTemplate(input_variables=["natural_language_text", "data"], template=prompt_template)
        response_chain = LLMChain(prompt=prompt, llm=llm)

        # Format the data as a string for the prompt
        formatted_data = "\n\n".join([f"Data:\n{data_item}" for data_item in data])

        result = response_chain.run(natural_language_text=natural_language_text, data=formatted_data)
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


def startup_prompt():
    mysql_choice = input("Fetch all data from MySQL? (y/n): ")
    if mysql_choice.lower() == 'y':
        all_data = fetch_all_tables_data()
        for data_item in all_data:  # Changed to iterate over list
            process_and_index_data([data_item])  # Pass a list of one item to process_and_index_data

    files_choice = input("Fetch all data from files in the uploads directory? (y/n): ")
    if files_choice.lower() == 'y':
        files_data = fetch_from_files(UPLOADS_DIR)
        process_and_index_data(files_data)


def summarize_large_text(query, related_text):
    # Chunk the related text
    text_chunks = chunk_text(related_text)

    # Summarize each chunk
    summaries = [summarize_text(query, chunk) for chunk in text_chunks]

    # Aggregate summaries
    aggregated_summary = " ".join(summaries)

    # Check if the aggregated summary is within the token limit
    while len(tokenizer.encode(aggregated_summary)) > 1024:
        aggregated_summary = summarize_text(query, aggregated_summary)
    
    return aggregated_summary