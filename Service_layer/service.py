from utils.config import index_name, model, llm, UPLOADS_DIR, pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
import json
from utils.embeddings_utils import SentenceTransformerEmbedding
from datetime import datetime, date, time
from typing import List
from utils.config import logger
from utils.util_methods import QueryResponseStorage
from langchain.prompts import PromptTemplate
import httpx
class DataProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,  # Chunk size based on GPT-3.5 token limit
            chunk_overlap=20  # Overlap to maintain context between chunks
        )

        self.embedding = SentenceTransformerEmbedding(model)
        self.index = pinecone.Index(index_name)

    def process_and_index_data(self, data):
        try:
            if not data:
                logger.warning("No data to index.")
                return

            chunk_size = 500  # Define your chunk size
            batch_size = 40930  # Define batch size for upsert
            vectors = []

            for d in data:
                if isinstance(d, dict) and "data" in d:
                    data_string = json.dumps(d["data"], default=self.json_serialize)
                    source = d.get("source", "unknown")
                else:
                    data_string = str(d)  # Handle cases where d might be a string directly
                    source = "unknown"  # Default source for string data
               
                # Split data_string into chunks using text_splitter
                chunks = self.text_splitter.split_text(data_string)

                # Process each chunk
                for i, chunk in enumerate(chunks):
                    metadata = {"source": source, "chunk_id": i, "text": chunk}

                    embeddings = self.embedding.embed_documents(chunk)

                    vectors.append({
                        "id": f"{source}#{i}",
                        "values": embeddings,
                        "metadata": metadata
                    })

                    # Check if batch size is reached
                    if len(vectors) >= batch_size:
                        # Upsert batch to Pinecone
                        self.index.upsert(
                            vectors=vectors,
                            namespace='task1'
                        )
                        print(f"Batch of {batch_size} indexed successfully.")
                        vectors = []
            # Upsert any remaining vectors
            if vectors:
                self.index.upsert(
                    vectors=vectors,
                    namespace='task1'
                )
                print(f"Final batch of {len(vectors)} indexed successfully.")

            print("Data indexed successfully in Pinecone.")
            return "File upload successfully!"
        except Exception as e:
            logger.error(f"Error processing and indexing data: {e}")
            raise

    @staticmethod
    def json_serialize(obj):
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def convert_to_natural_language(self, data: List[str], natural_language_text: str) -> List[str]:
        try:
            if not data:
                return ["No data present in the database for the given prompt. Please provide correct data."]

            # Combine all data items into a single string
            full_text = " ".join(data)

            # Split the full text into manageable chunks
            text_chunks = self.text_splitter.split_text(full_text)

            print("Number of chunks are: ", len(text_chunks))

            # Fetch the most recent query and response from MongoDB or another storage
            recent_query, recent_response = QueryResponseStorage.fetch_recent_query_response()

            # Define the prompt template
            prompt_template = """
            You are a helpful assistant tasked with reviewing chunks of text to identify and perform specific tasks based on the user's query.

            Here is the user's query in the form of a natural language request:
            {natural_language_text}

            Here are the most recent previous user query and its response:
            Previous Query: {recent_query}
            Previous Response: {recent_response}

            Below are the chunks of text:
            {data}

Instructions:
- For each chunk of text, determine if it contains relevant information that answers the user's query.
- If the query requests a task like counting, summarize or analysis, perform the required task and provide the result.
- Use the previous query and response if they are relevant; otherwise, ignore them.
- If a chunk contains relevant information, extract and return only the information that directly addresses the query.
- If a chunk does not contain relevant information, return "No answer in this chunk."
- Do not add any additional information, explanations, or context.
- Ensure that each returned result is concise and within a 20-word limit.
"""

            # Create the prompt using the PromptTemplate
            prompt = PromptTemplate(
                input_variables=["natural_language_text", "recent_query", "recent_response", "data"],
                template=prompt_template
            )

            # Initialize the response chain with the LLM and prompt
            response_chain = LLMChain(prompt=prompt, llm=llm)

            # Collect responses for each chunk
            responses = []
            for data_chunk in text_chunks:
              formatted_data = f"Data:\n{data_chunk}"
              response = response_chain.run(
                natural_language_text=natural_language_text,
                recent_query=recent_query,
                recent_response=recent_response,
                data=formatted_data
            )
              responses.append(response.strip())
        
            return responses

        except Exception as e:
            logger.error(f"Unexpected error in generating natural response: {e}")
            raise

    def final_response(self, intermediate_responses: List[str], natural_language_text: str) -> str:
        try:
            # Fetch the most recent query and response from MongoDB or another storage
            recent_query, recent_response = QueryResponseStorage.fetch_recent_query_response()

            # Combine the intermediate responses into a single string
            combined_data = "\n\n".join(intermediate_responses)

            # Define the final prompt template
            final_prompt_template = """
            You are a helpful assistant that synthesizes multiple intermediate responses into a final concise and precise natural language response.

            Here is the user's query in the form of a natural language request:
            {natural_language_text}

            Here are the most recent previous user query and its response:
            Previous Query: {recent_query}
            Previous Response: {recent_response}

            Below are the combined intermediate responses:
            {data}

Instructions:
- Carefully review the combined intermediate responses.
- Extract and synthesize the relevant information to generate a clear and direct answer to the user's query.
- Perform any required tasks based on the query, such as analysis, summarization, counting, adding or prediction, using the intermediate responses.
- Ensure that your response is concise and directly addresses the query based on the provided information.
- Also, review the recent Previous Query and its Response, and if they are helpful, use their information in the final response; otherwise, avoid these.
- If the combined responses do not contain relevant information or if no answer can be derived, respond with: "No information available, please provide a correct prompt."
- Avoid adding any extra information, context, or explanations.
- Do not start the response with phrases like "Based on the provided query results" or similar.
- Provide a final response in a single sentence format, based solely on the combined intermediate responses.
"""

            # Create the final prompt using the PromptTemplate
            final_prompt = PromptTemplate(
                input_variables=["natural_language_text", "recent_query", "recent_response", "data"],
                template=final_prompt_template
            )

            # Initialize the final response chain with the LLM and final prompt
            final_response_chain = LLMChain(prompt=final_prompt, llm=llm)

            # Generate the final response
            final_response = final_response_chain.run(
                natural_language_text=natural_language_text,
                recent_query=recent_query,
                recent_response=recent_response,
                data="\n\n".join(intermediate_responses)
            )
            # Store the final query and response in MongoDB or another storage
            QueryResponseStorage.store_query_response(natural_language_text, final_response.strip())
            return final_response.strip()

        except Exception as e:
            logger.error(f"Unexpected error in generating final response: {e}")
            raise
