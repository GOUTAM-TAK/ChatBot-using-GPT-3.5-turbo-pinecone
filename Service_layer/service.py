from utils.config import index_name, model, llm, UPLOADS_DIR
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from utils.embeddings_utils import SentenceTransformerEmbedding
from datetime import datetime,date
from typing import List
from utils.config import logger

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
            namespace='task1',
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