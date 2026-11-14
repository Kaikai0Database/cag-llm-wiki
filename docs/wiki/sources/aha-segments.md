# AHA 16-Segment Coronary Tree Classification and Anatomical Standard

- id：`aha-segments`
- 原始檔：`raw/02-aha-16-segment.md`
- 引用：Austen WG, et al. A reporting system on patients evaluated for coronary artery disease. Circulation. 1975;51(4 Suppl):5-40. ; Raff GL, et al. SCCT guidelines for the interpretation and reporting of coronary computed tomographic angiography. J Cardiovasc Comput Tomogr. 2009;3(2):122-136.
- 備註：本檔為專案整理稿（非原文全文），分段編號採 SCCT 2009 修訂之 16 分段版本。使用前請以原文核對。

## 導讀（LLM 生成，已過數字檢查；檢核依據是下方原文段落）

AHA 16 分段系統用於統一描述冠狀動脈病灶位置，使不同機構間可進行比較，AI 模型需依此標準進行分段標註。該系統包含 16 個分段，並根據冠狀動脈優勢型態影響部分段落的存在。

關鍵詞：右冠狀動脈（RCA）、左主幹與左前降支（LM / LAD）、左迴旋支（LCx）、優勢型態、狹窄程度分級、SYNTAX Score、分段對照表

## 原文段落（檢索與交叉檢查的依據）

### `aha-segments#1` 分段系統的目的

美國心臟協會（AHA）於 1975 年提出冠狀動脈分段報告系統，用統一的編號描述病灶位置，讓不同醫師、不同醫院與研究之間可以比較。後續 SCCT 2009 冠狀動脈電腦斷層判讀指引採用修訂的 16 分段版本。AI 模型的分段標註也需要固定的命名標準，才能與臨床報告對齊。

### `aha-segments#2` 右冠狀動脈（RCA）分段

第 1 段：RCA 近端（proximal RCA）。第 2 段：RCA 中段（mid RCA）。第 3 段：RCA 遠端（distal RCA）。第 4 段：右側後降支（R-PDA）。第 16 段：右側後側支（R-PLB）。

### `aha-segments#3` 左主幹與左前降支（LM / LAD）分段

第 5 段：左主幹（left main, LM）。第 6 段：LAD 近端。第 7 段：LAD 中段。第 8 段：LAD 遠端。第 9 段：第一對角支（D1）。第 10 段：第二對角支（D2）。

### `aha-segments#4` 左迴旋支（LCx）分段

第 11 段：LCx 近端。第 12 段：第一鈍緣支（OM1）。第 13 段：LCx 中遠端。第 14 段：第二鈍緣支（OM2）。第 15 段：左側後降支（L-PDA）。

### `aha-segments#5` 優勢型態

冠狀動脈優勢（dominance）由供應後降支（PDA）的血管決定：由 RCA 供應為右優勢，由 LCx 供應為左優勢，兩者共同供應為共同優勢（co-dominant）。優勢型態會影響第 4、15、16 段是否存在，AI 分段模型需要能處理這些變異。

### `aha-segments#6` 狹窄程度分級

AHA 1975 報告系統以管腔直徑縮減百分比描述狹窄，分級為 0、25%、50%、75%、90%、99%（次全阻塞）與 100%（完全阻塞）。臨床慣例上，左主幹直徑狹窄 ≥50%、其他心外膜血管 ≥70% 視為顯著狹窄。

### `aha-segments#7` 與 AI 標註資料集的對應

部分公開血管造影 AI 資料集（例如 ARCADE）採用 SYNTAX Score 的分段定義，分段數目與 AHA 16 分段不同。建置模型時需要建立分段對照表，把模型輸出轉換成臨床報告使用的編號。
