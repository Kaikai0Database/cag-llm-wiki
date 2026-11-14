"""HTML 簡報生成節點：把通過檢核的內容寫成 docs/ 下的 JSON（頁面再用 textContent 渲染）。"""
import json
import re
from datetime import datetime
from pathlib import Path

SLUG = re.compile(r"^[a-z0-9-]+$")
FIGURE_SRC = re.compile(r"^img/[a-z0-9-]+\.svg$")  # 只允許 docs/img 下的本地 SVG


def _clean_slide(slide):
    """figure 路徑不合法就整個拿掉，不讓外部或奇怪的路徑進網頁。"""
    fig = slide.get("figure")
    if fig is None:
        return slide
    out = {k: v for k, v in slide.items() if k != "figure"}
    if isinstance(fig, dict) and FIGURE_SRC.match(str(fig.get("src", ""))) and fig.get("alt"):
        out["figure"] = {"src": fig["src"], "alt": str(fig["alt"]), "caption": str(fig.get("caption", ""))}
    return out


def _read(path, default):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def _write(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_deck(state, docs_dir, model):
    spec = state["spec"]
    slug = spec["slug"]
    if not SLUG.match(slug):
        raise ValueError(f"slug 只能用小寫英數與 -：{slug}")
    docs_dir = Path(docs_dir)
    now = datetime.now().isoformat(timespec="seconds")
    used = {}
    for s in state["slides"]:
        for b in s["bullets"]:
            c = state["chunks_used"].get(b["cite"]["chunk_id"], {})
            used.setdefault(b["cite"]["source_id"], {
                "source_id": b["cite"]["source_id"], "title": b["cite"]["source_title"],
                "citation": c.get("citation", "")})
    rep = state["report"]
    verification = {"kept": rep["kept"], "dropped": len(rep["dropped"]),
                    "iterations": rep["iterations"], "empty_sections": rep["empty_sections"]}
    title_slide = {"type": "title", "title": spec["title"], "subtitle": spec.get("subtitle", ""),
                   "tags": spec.get("tags", [])}
    if spec.get("cover"):
        title_slide["figure"] = spec["cover"]
    slides = ([_clean_slide(title_slide)]
              + [_clean_slide(s) for s in state["slides"]]
              + [{"type": "references", "title": "參考資料與檢核紀錄",
                  "items": list(used.values()), "verification": verification}])
    deck = {"slug": slug, "title": spec["title"], "subtitle": spec.get("subtitle", ""),
            "generated_at": now, "model": model, "slides": slides}
    _write(docs_dir / "data" / "decks" / f"{slug}.json", deck)

    site_path = docs_dir / "data.json"
    site = _read(site_path, {"site": {}, "decks": [], "sources": []})
    entry = {"slug": slug, "title": spec["title"], "subtitle": spec.get("subtitle", ""),
             "tags": spec.get("tags", []), "slide_count": len(slides), "generated_at": now,
             "model": model, "verification": verification}
    site["decks"] = [d for d in site.get("decks", []) if d.get("slug") != slug] + [entry]
    _write(site_path, site)
    _write_report(docs_dir / "reports" / f"{slug}-verify.md", spec, rep, now, model)
    return deck


def _write_report(path, spec, rep, now, model):
    lines = [f"# 交叉檢查報告：{spec['title']}", "",
             f"- 產生時間：{now}", f"- 模型：{model}", f"- 迭代次數：{rep['iterations']}",
             f"- 保留重點：{rep['kept']}", f"- 剔除重點：{len(rep['dropped'])}",
             f"- 無內容章節：{', '.join(rep['empty_sections']) or '無'}", "",
             "## 剔除清單", "", "| 章節 | 引用 | 內容 | 原因 |", "|---|---|---|---|"]
    for d in rep["dropped"]:
        cells = [d["section"], d.get("chunk_id", ""), d.get("text", ""), d["reason"]]
        lines.append("| " + " | ".join(str(x).replace("|", "／").replace("\n", " ") for x in cells) + " |")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
