from datetime import datetime
from utils.config import collection, logger

class QueryResponseStorage:
    @staticmethod
    def store_query_response(query, response):
        try:
            if response == "No information available, please provide a correct prompt.":
                return
            document = {
                "query": query,
                "response": response,
                "timestamp": datetime.utcnow()
            }
            collection.insert_one(document)
            return True
        except Exception as e:
            logger.error(f"Error storing query and response: {e}")
            return False

    @staticmethod
    def fetch_recent_query_response():
        try:
            # Sort documents by timestamp in descending order and get the most recent one
            document = collection.find_one(sort=[("timestamp", -1)])
            if document:
                return document['query'], document['response']
            else:
                return None, None
        except Exception as e:
            logger.error(f"Error fetching recent query and response: {e}")
            return None, None
