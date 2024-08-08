from utils.config import logger
# Define a custom embedding function wrapper
class SentenceTransformerEmbedding:
    def __init__(self, model):
        self.model = model

    def embed_documents(self, documents):
        try:
          return self.model.encode(documents, show_progress_bar=True, convert_to_numpy=True).tolist()
        except Exception as e:
            logger.error(f"error in embed_documents : {e}")
            raise

    def embed_query(self, query):
        try:

          if isinstance(query, str):
            return self.model.encode([query], show_progress_bar=True, convert_to_numpy=True).tolist()[0]
          else:
            raise ValueError("Query must be a string")
        except Exception as e:
           logger.error(f"error in embed_query : {e}")
           raise