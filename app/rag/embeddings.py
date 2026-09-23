"""Embedding adapters. local_hash is deterministic test infrastructure, not semantic quality."""
import hashlib
import math
import re
from app import config

def _normalize(v):
    norm = math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/norm for x in v]

class LocalHashEmbedding:
    def __init__(self, dim=256):
        self.dim = dim

    def embed(self, text):
        vec = [0.0] * self.dim
        for token in re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9_]+", text.lower()):
            h = int(hashlib.sha256(token.encode()).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        return _normalize(vec)

class OpenAIEmbedding:
    def __init__(self):
        # Lazy import keeps zero-key/local tests runnable without optional SDK imports.
        from openai import OpenAI
        self.client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)

    def embed(self, text):
        return self.client.embeddings.create(model=config.EMBEDDING_MODEL, input=text).data[0].embedding

def build_embedding_provider():
    if config.EMBEDDING_PROVIDER == "local_hash":
        return LocalHashEmbedding(config.EMBEDDING_DIM)
    if config.EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbedding()
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER={config.EMBEDDING_PROVIDER}")
