from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class TFIDFRetriever:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.chunks = []
        self.tfidf_matrix = None

    def index_chunks(self, chunks):
        self.chunks = chunks
        if not chunks:
            return
        texts = [chunk["text"] for chunk in chunks]
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)

    def search(self, query, top_k=5, threshold=0.1):
        if self.tfidf_matrix is None or not self.chunks:
            return []
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if similarities[idx] >= threshold:
                results.append({
                    "chunk": self.chunks[idx],
                    "score": float(similarities[idx])
                })
        return results
