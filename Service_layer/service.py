from utils.config import index_name, model, llm, UPLOADS_DIR,pinecone
from langchain_pinecone import PineconeVectorStore
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain import PromptTemplate
from langchain.schema import Document  # Correct import for Document
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
# Text Splitter: Break down the text into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=3000,  # Chunk size based on GPT-3.5 token limit
    chunk_overlap=20  # Overlap to maintain context between chunks
)

# Function to convert database results into a natural language response
# Function to convert database results into a natural language response
def convert_to_natural_language(data: List[str], natural_language_text: str) -> str:
    try:
        if not data:
            return "No data present in the database for the given prompt. Please provide correct data."

        # Fetch the most recent query and response from MongoDB or another storage
        recent_query, recent_response = fetch_recent_query_response()

        # Default messages if recent query or response is not available
        if not recent_query:
            recent_query = "No previous query available."
        if not recent_response:
            recent_response = "No previous response available."

        # Combine all data into a single string
        full_text = " ".join(data)

        # Split the text into manageable chunks
        text_chunks = text_splitter.split_text(full_text)

        # Prepare documents for summarization
        docs = [Document(page_content=t) for t in text_chunks]

        # Log or print the number of chunks created
        num_chunks = len(docs)
        print(f"Number of document chunks created: {num_chunks}")

        # Define the prompt template
        map_prompt_template = """
        Based on the provided chunk of text, answer the following query: {user_query}.
        Text: {text}
        """

        reduce_prompt_template = """
       Combine the following responses to answer the user's query concisely.

       User Query: {user_query}

       Mapped Responses:
       {mapped_responses}
       """

        # Initialize PromptTemplates
        map_prompt = PromptTemplate(
            input_variables=["user_query", "text"],
            template=map_prompt_template
        )

        combine_prompt = PromptTemplate(
            input_variables=["user_query", "mapped_responses"],
            template=reduce_prompt_template
        )

        # Load the Map-Reduce Chain with the custom prompts
        chain = load_summarize_chain(
            llm=llm,
            chain_type="map_reduce",
            map_prompt=map_prompt,
            combine_prompt=combine_prompt,
            input_key="input_documents",
            output_key="output_text"
        )

        # Run the chain
        result = chain.invoke({
            "input_documents": docs,
            "user_query": natural_language_text
        }, return_only_outputs=True)

        # Extract the summary from the result
        final_summary = result.get("output_text", "").strip()

        # If no relevant information was found
        if not final_summary:
            final_summary = "No information available, please provide a correct prompt."

        # Store the query and final summary into MongoDB or another storage
        store_query_response(natural_language_text, final_summary)

        return final_summary
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
