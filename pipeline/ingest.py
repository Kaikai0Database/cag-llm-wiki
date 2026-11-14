"""Ingest：raw/*.md → docs/wiki/（段落、向量、每篇來源頁、索引、日誌）＋ docs/data.json 的 sources。"""
import json
from datetime import datetime
from pathlib import Path

from . import config
from .render import _read, _write
from .verify import numbers_ok
from .wiki import load_sources

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"},
                   "key_terms": {"type": "array", "items": {"type": "string"}}},
    "required": ["summary", "key_terms"],
}

SITE_DEFAULT = {
    "title": "CAG AI 影像分析 × 2024 ESC 知識庫",
    "subtitle": "本機 LLM Wiki 與教學簡報（Ollama，零雲端）",
}


def _summarize(llm, src):
    body = "\n".join(f"## {c['heading']}\n{c['text']}" for c in src["chunks"])
    out = llm.chat_json(
        "你是知識庫編輯。只根據提供的文件寫導讀，不可加入文件外的知識。",
        f"文件：{src['title']}\n\n{body}\n\n"
        "請輸出：summary＝繁體中文 2 到 3 句導讀（數字必須與原文一致）；"
        "key_terms＝5 到 8 個原文中出現過的關鍵詞（照原文寫法）。",
        SUMMARY_SCHEMA)
    full = " ".join(c["heading"] + " " + c["text"] for c in src["chunks"])
    summary = out.get("summary", "").strip()
    ok, missing = numbers_ok(summary, full)
    terms = [t for t in out.get("key_terms", []) if isinstance(t, str) and t and t.lower() in full.lower()]
    notes = []
    if not ok:
        notes.append(f"導讀含原文沒有的數字 {missing}，已捨棄")
        summary = ""
    dropped_terms = len(out.get("key_terms", [])) - len(terms)
    if dropped_terms:
        notes.append(f"捨棄 {dropped_terms} 個原文沒有的關鍵詞")
    return summary, terms[:8], notes


def _source_page(src, summary, terms):
    lines = [f"# {src['title']}", "", f"- id：`{src['id']}`", f"- 原始檔：`raw/{src['file']}`",
             f"- 引用：{src['citation']}", f"- 備註：{src.get('note', '')}", ""]
    if summary:
        lines += ["## 導讀（LLM 生成，已過數字檢查；檢核依據是下方原文段落）", "", summary, ""]
    if terms:
        lines += ["關鍵詞：" + "、".join(terms), ""]
    lines += ["## 原文段落（檢索與交叉檢查的依據）", ""]
    for c in src["chunks"]:
        lines += [f"### `{c['id']}` {c['heading']}", "", c["text"], ""]
    return "\n".join(lines)


def run(llm=None, embedder=None, log=print):
    sources = load_sources(config.RAW_DIR)
    chunks = [c for s in sources for c in s["chunks"]]
    wiki = config.WIKI_DIR
    _write(wiki / "chunks.json", chunks)
    log(f"[ingest] {len(sources)} 篇來源，{len(chunks)} 個段落")

    if embedder:
        vecs = embedder([f"{c['heading']}\n{c['text']}" for c in chunks])
        _write(wiki / "embeddings.json", {"model": getattr(embedder, "model", ""),
                                          "vectors": {c["id"]: v for c, v in zip(chunks, vecs)}})
        log(f"[ingest] 已建立 {len(vecs)} 個向量")

    now = datetime.now().isoformat(timespec="seconds")
    site_sources, log_lines = [], [f"## {now} ingest"]
    for src in sources:
        summary, terms, notes = _summarize(llm, src) if llm else ("", [], [])
        (wiki / "sources").mkdir(parents=True, exist_ok=True)
        (wiki / "sources" / f"{src['id']}.md").write_text(_source_page(src, summary, terms), encoding="utf-8")
        site_sources.append({"id": src["id"], "title": src["title"], "citation": src["citation"],
                             "note": src.get("note", ""), "chunk_count": len(src["chunks"]),
                             "summary": summary, "key_terms": terms,
                             "wiki_page": f"wiki/sources/{src['id']}.md"})
        log_lines.append(f"- `{src['id']}`：{len(src['chunks'])} 段" + (f"；{'；'.join(notes)}" if notes else ""))
        log(f"[ingest] {src['id']} 完成" + (f"（{'；'.join(notes)}）" if notes else ""))

    index = ["# Wiki 索引", "", "| id | 標題 | 段落數 |", "|---|---|---|"]
    index += [f"| [{s['id']}](sources/{s['id']}.md) | {s['title']} | {s['chunk_count']} |" for s in site_sources]
    (wiki / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    log_path = wiki / "log.md"
    old = log_path.read_text(encoding="utf-8") if log_path.exists() else "# Wiki 變更日誌\n"
    log_path.write_text(old.rstrip("\n") + "\n\n" + "\n".join(log_lines) + "\n", encoding="utf-8")

    site_path = config.DOCS_DIR / "data.json"
    site = _read(site_path, {"site": SITE_DEFAULT, "decks": [], "sources": []})
    site.setdefault("site", SITE_DEFAULT)
    site["sources"] = site_sources
    site["wiki_updated_at"] = now
    _write(site_path, site)
    return sources


def load_index():
    wiki = config.WIKI_DIR
    chunks = json.loads((wiki / "chunks.json").read_text(encoding="utf-8"))
    emb_path = wiki / "embeddings.json"
    emb = json.loads(emb_path.read_text(encoding="utf-8"))["vectors"] if emb_path.exists() else None
    return chunks, emb
