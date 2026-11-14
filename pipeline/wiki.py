"""解析 raw/ 原始資料成 Wiki 段落（chunk）。raw/ 視為不可變，只讀不寫。"""
import re
from pathlib import Path


def parse_source(path):
    text = Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", text, flags=re.S)
    if not m:
        raise ValueError(f"{path} 缺少 front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    for key in ("id", "title", "citation"):
        if not meta.get(key):
            raise ValueError(f"{path} front matter 缺少 {key}")
    chunks = []
    for part in re.split(r"^## ", m.group(2), flags=re.M)[1:]:
        heading, _, body = part.partition("\n")
        body = " ".join(body.split())
        if body:
            chunks.append({
                "id": f"{meta['id']}#{len(chunks) + 1}",
                "source_id": meta["id"],
                "source_title": meta["title"],
                "citation": meta["citation"],
                "heading": heading.strip(),
                "text": body,
            })
    return {**meta, "file": Path(path).name, "chunks": chunks}


def load_sources(raw_dir):
    return [parse_source(p) for p in sorted(Path(raw_dir).glob("*.md"))]
