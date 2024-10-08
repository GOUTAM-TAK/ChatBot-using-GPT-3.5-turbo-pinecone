from sentence_transformers import SentenceTransformer
from langchain_community.chat_models import ChatOpenAI
from pinecone import Pinecone,ServerlessSpec
import os
import logging
from pymongo import MongoClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Load the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Constants
UPLOADS_DIR = "./uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

#set environment variable
os.environ['PINECONE_API_KEY'] = "b807b048-2024-47bd-b4d5-c94e5f982ec"
pinecone_api_key = os.getenv('PINECONE_API_KEY')
index_name = "training-project-vectordb"
spec = ServerlessSpec(region="us-east-1", cloud="aws")
name_space = 'task1'
# Initialize the language model
openai_api_key = os.getenv('OPENAI_API_KEY', 'your-openai-api-key')
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=openai_api_key)

# Initialize Pinecone
pinecone = Pinecone(api_key=pinecone_api_key)

#configure mongodb connection details
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "task1"
COLLECTION_NAME = "query_cache"

#create a MongoDB Client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
