"""處理圖：retrieve → extract → verify ─(通過率低且還有次數)→ extract
                                     └─(否則)→ assemble → END
"""
from . import config
from .verify import llm_judge, rule_check

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {"bullets": {"type": "array", "items": {
        "type": "object",
        "properties": {"text": {"type": "string"}, "chunk_id": {"type": "string"}},
        "required": ["text", "chunk_id"]}}},
    "required": ["bullets"],
}

EXTRACT_SYSTEM = (
    "你是醫學教育簡報的內容整理員。只能根據使用者提供的證據段落寫重點，"
    "禁止使用段落以外的知識，禁止推測。"
)


def _extract_prompt(sec):
    chunks = "\n".join(f'<chunk id="{c["id"]}" heading="{c["heading"]}">{c["text"]}</chunk>'
                       for c in sec["chunks"])
    fb = ""
    if sec["rejected"]:
        fb = "\n上一輪被剔除的重點與原因（不要再犯）：\n" + "\n".join(
            f"- {d['text']} → {d['reason']}" for d in sec["rejected"][-6:])
    return (
        f"簡報章節：{sec['title']}\n章節焦點：{sec['query']}\n\n證據段落：\n{chunks}\n\n"
        "請寫 3 到 5 個教學重點，規則：\n"
        "1. 使用繁體中文，每點不超過 60 字，可保留英文專有名詞。\n"
        "2. 每點的 chunk_id 必須是上面出現過的 id，且該段落要能直接支持這一點。\n"
        "3. 數字、單位、標籤編號必須與段落完全一致，不可自行推算或新增。\n"
        "4. 段落沒寫的推薦等級、比例、結論一律不要寫。\n"
        "5. text 裡不要寫 chunk_id 或括號引用，引用只放在 chunk_id 欄位。" + fb
    )


def node_retrieve(state, ctx):
    for sec in state["sections"]:
        sec["chunks"] = ctx["retriever"](sec["query"], k=sec.get("k", config.TOP_K),
                                         sources=sec.get("sources"))
    return "extract"


def node_extract(state, ctx):
    state["iter"] += 1
    for sec in state["sections"]:
        if sec["done"] or not sec["chunks"]:
            continue
        out = ctx["llm"].chat_json(EXTRACT_SYSTEM, _extract_prompt(sec), EXTRACT_SCHEMA)
        sec["candidates"] = [b for b in out.get("bullets", []) if isinstance(b, dict)]
    return "verify"


def node_verify(state, ctx):
    for sec in state["sections"]:
        if sec["done"]:
            continue
        cands, sec["candidates"] = sec.get("candidates", []), []
        chunk_map = {c["id"]: c for c in sec["chunks"]}
        passed_rules = []
        for b in cands:
            reason, text = rule_check(b, chunk_map)
            if reason:
                sec["rejected"].append({"text": b.get("text", ""), "chunk_id": b.get("chunk_id", ""),
                                        "reason": f"規則：{reason}"})
            else:
                passed_rules.append({"text": text, "chunk_id": b["chunk_id"].strip()})
        verdicts = llm_judge(ctx["llm"], passed_rules, chunk_map)
        seen = {k["text"] for k in sec["kept"]}
        new_kept = 0
        for b, (ok, why) in zip(passed_rules, verdicts):
            if not ok:
                sec["rejected"].append({**b, "reason": f"審查：{why}"})
            elif b["text"] not in seen:
                seen.add(b["text"])
                c = chunk_map[b["chunk_id"]]
                sec["kept"].append({"text": b["text"], "cite": {
                    "chunk_id": c["id"], "source_id": c["source_id"],
                    "source_title": c["source_title"], "heading": c["heading"]}})
                new_kept += 1
        rate = (sum(1 for _, (ok, _w) in zip(passed_rules, verdicts) if ok) / len(cands)) if cands else 0
        sec["pass_rate"] = rate
        if rate >= config.PASS_THRESHOLD and len(sec["kept"]) >= config.MIN_BULLETS:
            sec["done"] = True
    retry = any(not s["done"] and s["chunks"] for s in state["sections"])
    return "extract" if retry and state["iter"] < ctx["max_iters"] else "assemble"


def node_assemble(state, ctx):
    state["slides"] = []
    dropped, empty = [], []
    for sec in state["sections"]:
        for d in sec["rejected"]:
            dropped.append({"section": sec["title"], **d})
        if sec["kept"]:
            state["slides"].append({"type": "content", "title": sec["title"], "bullets": sec["kept"]})
        else:
            empty.append(sec["title"])
    kept = sum(len(s["bullets"]) for s in state["slides"])
    state["report"] = {"iterations": state["iter"], "kept": kept, "dropped": dropped,
                       "empty_sections": empty}
    state["chunks_used"] = {c["id"]: c for s in state["sections"] for c in s["chunks"]}
    return None


NODES = {"retrieve": node_retrieve, "extract": node_extract,
         "verify": node_verify, "assemble": node_assemble}


def run_deck(spec, llm, retriever, max_iters=config.MAX_ITERS, log=None):
    state = {"spec": spec, "iter": 0, "sections": [
        {**s, "chunks": [], "candidates": [], "kept": [], "rejected": [], "done": False}
        for s in spec["sections"]]}
    ctx = {"llm": llm, "retriever": retriever, "max_iters": max_iters}
    node = "retrieve"
    while node:
        if log:
            log(f"[graph] {node} (iter={state['iter']})")
        node = NODES[node](state, ctx)
    return state
