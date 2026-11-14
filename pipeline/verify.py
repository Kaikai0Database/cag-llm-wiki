"""交叉檢查與對齊：規則檢查（引用、數字）＋ LLM 審查。任何一關不過就剔除（fail closed）。"""
import re

_NUM = re.compile(r"\d+(?:\.\d+)?")
_FULLWIDTH = str.maketrans("０１２３４５６７８９．", "0123456789.")


def _nums(s):
    return set(_NUM.findall(s.translate(_FULLWIDTH)))


def numbers_ok(claim, chunk_text):
    """重點裡的每個數字都必須出現在引用段落中。"""
    missing = sorted(_nums(claim) - _nums(chunk_text))
    return (not missing), missing


JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"verdicts": {"type": "array", "items": {
        "type": "object",
        "properties": {"index": {"type": "integer"}, "supported": {"type": "boolean"},
                       "reason": {"type": "string"}},
        "required": ["index", "supported", "reason"]}}},
    "required": ["verdicts"],
}

JUDGE_SYSTEM = (
    "你是嚴格的醫學事實查核員。逐條判斷每個重點是否完全被它引用的證據段落支持。"
    "只要重點含有段落沒寫到的資訊、數字、推薦等級、因果推論或誇大，就判 supported=false。"
    "reason 用繁體中文簡短說明。"
)


# 模型常把引用編號抄進句子，例如「（esc2024#4）」；先移除，避免被當成數字
_ID_ECHO = re.compile(r"\s*[（(\[]?\s*(?:引用\s*)?[a-z0-9-]+#\d+\s*[）)\]]?", re.I)


def clean_text(text):
    return _ID_ECHO.sub("", text or "").strip(" ，,;；")


def rule_check(bullet, chunk_map):
    """回傳 (剔除原因或 None, 清理後文字)。數字可出現在段落內文、標題或來源標題。"""
    text = clean_text(bullet.get("text"))
    cid = (bullet.get("chunk_id") or "").strip()
    if not text:
        return "空白重點", text
    if cid not in chunk_map:
        return f"引用 {cid or '(空)'} 不在本節檢索到的段落中", text
    c = chunk_map[cid]
    ok, missing = numbers_ok(text, " ".join([c.get("source_title", ""), c.get("heading", ""), c["text"]]))
    if not ok:
        return f"數字 {', '.join(missing)} 不在引用段落 {cid} 中", text
    return None, text


def llm_judge(llm, bullets, chunk_map):
    """回傳與 bullets 等長的 (supported, reason) 清單；模型漏回的條目視為不支持。"""
    if not bullets:
        return []
    used = sorted({b["chunk_id"] for b in bullets})
    evidence = "\n".join(f'<chunk id="{cid}">{chunk_map[cid]["text"]}</chunk>' for cid in used)
    claims = "\n".join(f"[{i}] (引用 {b['chunk_id']}) {b['text']}" for i, b in enumerate(bullets))
    user = f"證據段落：\n{evidence}\n\n待查核的重點：\n{claims}\n\n請對每一條輸出 verdict。"
    out = llm.chat_json(JUDGE_SYSTEM, user, JUDGE_SCHEMA)
    got = {v.get("index"): v for v in out.get("verdicts", []) if isinstance(v, dict)}
    result = []
    for i in range(len(bullets)):
        v = got.get(i)
        if v is None:
            result.append((False, "審查模型未回覆此條"))
        else:
            result.append((bool(v.get("supported")), str(v.get("reason", ""))))
    return result
