"""檢索：有嵌入向量就用 cosine；沒有（Ollama 沒開）就退回字元 bigram 比對。"""
import math


def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _bigrams(s):
    s = "".join(s.lower().split())
    return {s[i:i + 2] for i in range(len(s) - 1)}


class Retriever:
    def __init__(self, chunks, embeddings=None, embedder=None):
        self.chunks = chunks
        self.embeddings = embeddings  # dict: chunk_id -> vector
        self.embedder = embedder

    def __call__(self, query, k=4, sources=None):
        pool = [c for c in self.chunks if not sources or c["source_id"] in sources]
        if self.embeddings and self.embedder:
            q = self.embedder([query])[0]
            scored = [(_cos(q, self.embeddings[c["id"]]), c) for c in pool if c["id"] in self.embeddings]
        else:
            qb = _bigrams(query)
            scored = [(len(qb & _bigrams(c["heading"] + c["text"])), c) for c in pool]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:k]]
