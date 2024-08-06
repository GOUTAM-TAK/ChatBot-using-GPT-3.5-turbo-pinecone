# Define a custom embedding function wrapper
class SentenceTransformerEmbedding:
    def __init__(self, model):
        self.model = model

    def embed_documents(self, documents):
        return self.model.encode(documents, show_progress_bar=True, convert_to_numpy=True).tolist()

    def embed_query(self, query):
        if isinstance(query, str):
            return self.model.encode([query], show_progress_bar=True, convert_to_numpy=True).tolist()[0]
        else:
            raise ValueError("Query must be a string")