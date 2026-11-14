"""本機 Ollama 用戶端（只用 HTTP，不依賴任何雲端 SDK）。"""
import json
from urllib.parse import urlparse

import requests

from . import config


def _check_local(url):
    host = urlparse(url).hostname
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError(f"OLLAMA_URL 必須是本機位址，收到：{url}")
    return url.rstrip("/")


class OllamaLLM:
    def __init__(self, model=None, url=None, temperature=0.1):
        self.model = model or config.CHAT_MODEL
        self.url = _check_local(url or config.OLLAMA_URL)
        self.temperature = temperature

    def chat_json(self, system, user, schema):
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "format": schema,           # Ollama structured output
            "stream": False,
            "options": {"temperature": self.temperature, "num_ctx": 8192},
        }
        if self.model.startswith("qwen3"):
            body["think"] = False
        r = requests.post(f"{self.url}/api/chat", json=body, timeout=900)
        r.raise_for_status()
        return json.loads(r.json()["message"]["content"])


class OllamaEmbedder:
    def __init__(self, model=None, url=None):
        self.model = model or config.EMBED_MODEL
        self.url = _check_local(url or config.OLLAMA_URL)

    def __call__(self, texts):
        r = requests.post(f"{self.url}/api/embed",
                          json={"model": self.model, "input": list(texts)}, timeout=900)
        r.raise_for_status()
        return r.json()["embeddings"]
