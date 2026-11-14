"""用法：
  python -m pipeline ingest [--no-llm] [--no-embed]
  python -m pipeline build decks/cag-esc-2024.json [--model qwen3:8b]
"""
import argparse
import json
import sys
from pathlib import Path

from . import config, ingest
from .graph import run_deck
from .llm import OllamaEmbedder, OllamaLLM
from .render import write_deck
from .retrieve import Retriever


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ingest")
    a.add_argument("--no-llm", action="store_true", help="不產生 LLM 導讀")
    a.add_argument("--no-embed", action="store_true", help="不建向量（檢索改用字元比對）")
    a.add_argument("--model", default=config.CHAT_MODEL)
    b = sub.add_parser("build")
    b.add_argument("spec")
    b.add_argument("--model", default=config.CHAT_MODEL)
    b.add_argument("--max-iters", type=int, default=config.MAX_ITERS)
    args = ap.parse_args(argv)

    if args.cmd == "ingest":
        ingest.run(llm=None if args.no_llm else OllamaLLM(args.model),
                   embedder=None if args.no_embed else OllamaEmbedder())
        return 0

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    chunks, emb = ingest.load_index()
    retriever = Retriever(chunks, emb, OllamaEmbedder() if emb else None)
    state = run_deck(spec, OllamaLLM(args.model), retriever, max_iters=args.max_iters, log=print)
    write_deck(state, config.DOCS_DIR, model=args.model)
    r = state["report"]
    print(f"[build] {spec['slug']}：保留 {r['kept']} 點，剔除 {len(r['dropped'])} 點，"
          f"迭代 {r['iterations']} 次，空章節 {r['empty_sections'] or '無'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
