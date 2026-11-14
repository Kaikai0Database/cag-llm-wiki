import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
DOCS_DIR = ROOT / "docs"
WIKI_DIR = DOCS_DIR / "wiki"
DECKS_SPEC_DIR = ROOT / "decks"

# 只允許本機 Ollama；可用環境變數覆寫模型
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
CHAT_MODEL = os.environ.get("CAG_CHAT_MODEL", "qwen3:8b")
EMBED_MODEL = os.environ.get("CAG_EMBED_MODEL", "bge-m3")

TOP_K = 4
PASS_THRESHOLD = 0.6   # 一節通過率低於此值 → 回到抽取節點重做
MIN_BULLETS = 2        # 一節通過的重點少於此數 → 重做
MAX_ITERS = 2
