"""離線測試：用假的 LLM 測 pipeline 邏輯，不需要 Ollama。

執行：python -m unittest discover -s tests -v
"""
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from pipeline import wiki, verify, graph, render  # noqa: E402


CHUNKS = [
    {"id": "esc2024#4", "source_id": "esc2024", "source_title": "ESC 2024",
     "heading": "侵入性冠狀動脈造影與功能評估",
     "text": "對於直徑狹窄 40–90% 的中間程度病灶，建議以 FFR 或 iFR 進行侵入性功能評估。"},
    {"id": "aha-segments#2", "source_id": "aha-segments", "source_title": "AHA",
     "heading": "右冠狀動脈（RCA）分段",
     "text": "第 1 段：RCA 近端。第 2 段：RCA 中段。第 3 段：RCA 遠端。"},
]


class FakeLLM:
    """抽取節點回傳一條真話＋一條捏造數字；審查節點（故意）全部說支持。"""

    def __init__(self):
        self.calls = []

    def chat_json(self, system, user, schema):
        props = schema.get("properties", {})
        self.calls.append(list(props))
        if "bullets" in props:
            return {"bullets": [
                {"text": "40–90% 中間病灶建議做 FFR 或 iFR 功能評估", "chunk_id": "esc2024#4"},
                {"text": "FFR 門檻為 0.75 且適用 95% 病人", "chunk_id": "esc2024#4"},  # 捏造數字
                {"text": "不存在的段落", "chunk_id": "nope#9"},  # 捏造引用
            ]}
        if "verdicts" in props:
            n = len(re.findall(r"^\[\d+\]", user, flags=re.M))
            return {"verdicts": [{"index": i, "supported": True, "reason": "ok"} for i in range(n)]}
        raise AssertionError("unexpected schema")


def fake_retriever(query, k=4, sources=None):
    return [c for c in CHUNKS if not sources or c["source_id"] in sources][:k]


class TestWikiParse(unittest.TestCase):
    def test_parse_raw_source_into_chunks(self):
        src = wiki.parse_source(ROOT / "raw" / "02-aha-16-segment.md")
        self.assertEqual(src["id"], "aha-segments")
        self.assertTrue(src["citation"])
        self.assertGreaterEqual(len(src["chunks"]), 5)
        self.assertEqual(src["chunks"][0]["id"], "aha-segments#1")
        self.assertTrue(all(c["text"] and c["heading"] for c in src["chunks"]))

    def test_all_five_sources_present(self):
        self.assertEqual(len(wiki.load_sources(ROOT / "raw")), 5)


class TestVerify(unittest.TestCase):
    def test_numbers_must_exist_in_chunk(self):
        chunk = CHUNKS[0]["text"]
        ok, missing = verify.numbers_ok("40–90% 病灶做 FFR", chunk)
        self.assertTrue(ok, missing)
        ok, missing = verify.numbers_ok("FFR 門檻為 0.75", chunk)
        self.assertFalse(ok)
        self.assertIn("0.75", missing)

    def test_chunk_id_echo_and_title_year_are_not_hallucinations(self):
        chunk_map = {"esc2024#4": {**CHUNKS[0], "source_title": "2024 ESC Guidelines"}}
        b = {"text": "ESC 2024：40–90% 病灶做 FFR（esc2024#4）", "chunk_id": "esc2024#4"}
        reason, cleaned = verify.rule_check(b, chunk_map)
        self.assertIsNone(reason)
        self.assertEqual(cleaned, "ESC 2024：40–90% 病灶做 FFR")
        reason, _ = verify.rule_check({"text": "FFR ≤0.80（esc2024#4）", "chunk_id": "esc2024#4"}, chunk_map)
        self.assertIn("0.80", reason)


class TestGraph(unittest.TestCase):
    def test_crosscheck_drops_hallucinations(self):
        spec = {"slug": "t", "title": "T", "subtitle": "s",
                "sections": [{"title": "功能評估", "query": "FFR", "sources": ["esc2024"]}]}
        state = graph.run_deck(spec, llm=FakeLLM(), retriever=fake_retriever, max_iters=1)
        bullets = state["slides"][0]["bullets"]
        self.assertEqual([b["text"] for b in bullets], ["40–90% 中間病灶建議做 FFR 或 iFR 功能評估"])
        self.assertEqual(bullets[0]["cite"]["chunk_id"], "esc2024#4")
        reasons = " ".join(d["reason"] for d in state["report"]["dropped"])
        self.assertIn("0.75", reasons)
        self.assertIn("nope#9", reasons)

    def test_loop_retries_when_pass_rate_low(self):
        llm = FakeLLM()
        spec = {"slug": "t", "title": "T", "subtitle": "s",
                "sections": [{"title": "x", "query": "FFR", "sources": ["esc2024"]}]}
        graph.run_deck(spec, llm=llm, retriever=fake_retriever, max_iters=2)
        extracts = sum(1 for c in llm.calls if "bullets" in c)
        self.assertEqual(extracts, 2)  # 1/3 通過率 < 門檻 → 回頭重抽一次


class TestRender(unittest.TestCase):
    def test_deck_json_and_site_index(self):
        spec = {"slug": "t-deck", "title": "T", "subtitle": "s", "tags": ["CAG"],
                "sections": [{"title": "功能評估", "query": "FFR", "sources": ["esc2024"]}]}
        state = graph.run_deck(spec, llm=FakeLLM(), retriever=fake_retriever, max_iters=1)
        with tempfile.TemporaryDirectory() as d:
            docs = Path(d)
            (docs / "data").mkdir()
            (docs / "data.json").write_text(json.dumps({"site": {"title": "x"}, "decks": [], "sources": []}),
                                            encoding="utf-8")
            render.write_deck(state, docs, model="fake")
            deck = json.loads((docs / "data" / "decks" / "t-deck.json").read_text(encoding="utf-8"))
            types = [s["type"] for s in deck["slides"]]
            self.assertEqual(types[0], "title")
            self.assertEqual(types[-1], "references")
            site = json.loads((docs / "data.json").read_text(encoding="utf-8"))
            self.assertEqual(site["decks"][0]["slug"], "t-deck")
            self.assertEqual(site["decks"][0]["slide_count"], len(deck["slides"]))


class TestFrontendSafety(unittest.TestCase):
    """規範 4：禁止 innerHTML 類 API；外部來源必須寫死版本。"""

    def test_no_unsafe_dom_apis(self):
        bad = re.compile(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function")
        for js in (ROOT / "docs").glob("*.js"):
            self.assertIsNone(bad.search(js.read_text(encoding="utf-8")), js.name)

    def test_external_sources_are_version_pinned(self):
        url = re.compile(r"""(?:src|href)=["'](https?://[^"']+)["']""")
        for html in (ROOT / "docs").glob("*.html"):
            for u in url.findall(html.read_text(encoding="utf-8")):
                self.assertRegex(u, r"@\d+\.\d+\.\d+", f"{html.name}: {u} 沒寫死版本")


if __name__ == "__main__":
    unittest.main()
