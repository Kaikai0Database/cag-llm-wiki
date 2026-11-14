# CAG LLM Wiki × 教學 HTML 簡報

主題：冠狀動脈造影（CAG）AI 影像分析與 2024 ESC 臨床指引知識庫。
全部在本機執行：Ollama（`qwen3:8b` 文字、`bge-m3` 向量），沒有雲端 API，網頁也沒有外部 CDN。

## 目錄

```
raw/                 5 篇核心資料（輸入，pipeline 只讀不寫）
decks/               簡報主題設定（章節 + 檢索查詢 + 限定來源）
pipeline/            ingest / retrieve / extract / verify / render
tests/               離線測試（假 LLM，不需 Ollama）
docs/                所有頁面與產出
  index.html         首頁（頁首結構是其他頁面的範本）
  wiki.html          Wiki 段落瀏覽
  slides.html        簡報播放器
  style.css          共用樣式（只用 .card / .tag）
  common.js          共用工具（只用 textContent）
  img/*.svg          簡報用的圖（手繪 SVG，依 Wiki 段落繪製，不含程式碼與外部連結）
  data.json          網站資料：來源清單 + 簡報清單
  data/decks/*.json  每份簡報的擴充 JSON
  wiki/              chunks.json、embeddings.json、sources/*.md、index.md、log.md
  reports/           每份簡報的交叉檢查報告
```

## 處理圖（Loop / Graph）

```
retrieve ─→ extract ─→ verify ─┬─(某節通過率 < 60% 或少於 2 點，且還有次數)─→ extract
                                └─(否則)─→ assemble ─→ render(docs/)
```

- **retrieve**：用 bge-m3 向量（沒有向量時退回字元比對）從 Wiki 段落抓 top-k，可限定來源。
- **extract**：LLM 只能根據段落寫重點，每點必須填 `chunk_id`。
- **verify（交叉檢查與對齊）**，任一關不過就剔除：
  1. 引用的 `chunk_id` 必須是本節檢索到的段落；
  2. 重點裡每個數字都必須出現在該段落（或其標題、來源標題）；
  3. LLM 審查員逐條判斷「是否完全被段落支持」，漏回的條目視為不支持。
- **render**：寫 `docs/data/decks/<slug>.json`、更新 `docs/data.json`、寫 `docs/reports/<slug>-verify.md`。

## 使用

```powershell
$env:PYTHONUTF8="1"
python -m pipeline ingest                         # raw → docs/wiki（約 30 秒）
python -m pipeline build decks/cag-esc-2024.json  # 產生簡報（約 1–3 分鐘）
python -m unittest discover -s tests -v           # 離線測試
python -m http.server 8765 --bind 127.0.0.1 --directory docs   # 預覽 http://127.0.0.1:8765/
```

換模型：`$env:CAG_CHAT_MODEL="gemma4-12b-qat-local"`。`OLLAMA_URL` 只接受本機位址。

新增主題：複製 `decks/cag-esc-2024.json`，改 `slug`（小寫英數與 `-`）和章節，再跑 `build`。

簡報以圖為主：每個章節要有 `figure`（`src` 只能是 `img/<名稱>.svg`，`alt` 必填，`caption` 寫依據的段落）。
頁面上只露出 3 個重點，其餘收在「還有 N 點」。測試會檢查每章都有圖、圖檔存在，而且 SVG 裡沒有程式碼或外部連結。

## 部署（GitHub Pages）

網站：https://kaikai0database.github.io/cag-llm-wiki/

- `gh-pages` 分支 = `docs/` 的內容（用 `git subtree split` 產生），GitHub Pages 從這裡發佈。
- `source` 分支 = 完整原始碼。

更新網站：

```powershell
git subtree split --prefix docs -b site   # 每次重新產生
git push origin site:gh-pages main:source
git branch -D site
```

流程設計與反思：`docs/design.html`（資料在 `docs/data/design.json`）。

## 前端安全規範

- 資料只用 `textContent` / `createElement` 寫入；測試會掃描 `docs/*.js`，出現 `innerHTML`、`outerHTML`、`insertAdjacentHTML`、`document.write`、`eval(`、`new Function` 就失敗。
- 每頁都有 CSP：`script-src 'self'`，不允許 inline script 和外部來源。
- 連結只允許同源；`deck` 參數用白名單 regex，而且必須存在於 `data.json`。
- 目前沒有使用任何 CDN。若之後加入，網址必須寫死版本（例如 `pkg@1.2.3`），測試會檢查。

## 重要限制

- `raw/` 的 5 篇是**整理稿，不是原文**（每篇的 front matter 都有寫）。正式使用前請換成原文或你自己核對過的摘錄，然後重跑 `ingest` 和 `build`。
- LLM 審查員不是百分之百可靠。開發時曾漏掉一條把「功能性影像」寫成「排除 CAD」的錯誤，後來靠縮小檢索範圍修正。數字檢查是規則，比較可靠；語意檢查仍需要人工抽查。
- 簡報只能當教學材料，不能用來做臨床決策。
