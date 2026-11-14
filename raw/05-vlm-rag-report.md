---
id: vlm-rag
title: Vision-Language Models (VLMs) and RAG Integration for Medical Report Generation
citation: 綜合整理稿。參考：Lewis P, et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 2020.
note: 本檔為專案整理稿（方法學綜述，非單一論文原文）。
---

## 視覺語言模型的架構
視覺語言模型（vision-language model, VLM）通常由三部分組成：影像編碼器（vision encoder）把影像轉成特徵、投影層（projector）把影像特徵對齊到語言模型的向量空間、大型語言模型（LLM）根據影像特徵與文字提示產生文字。本機可用的開源 VLM 例如 Qwen2.5-VL。

## 檢索增強生成（RAG）
檢索增強生成（retrieval-augmented generation, RAG）在生成前先從外部知識庫檢索相關段落，再把段落放進提示中，讓模型根據證據回答。基本步驟為：切分文件（chunking）、以嵌入模型（embedding model）轉成向量、依問題檢索前 k 個最相似段落、把段落連同引用編號交給模型生成。本機可用的多語嵌入模型例如 bge-m3。

## RAG 對醫療報告的價值
醫療報告需要符合最新指引，而模型訓練資料可能過時。RAG 讓報告可以引用指引原文段落，並附上出處，方便醫師核對。知識庫更新時只需重新建立索引，不必重新訓練模型。

## 幻覺與防護
大型語言模型可能產生看似合理但沒有根據的內容，稱為幻覺（hallucination）。常見防護方法包括：要求每個結論附上引用段落編號、以第二階段模型或規則檢查結論是否被引用段落支持、檢查數字與單位是否出現在原文、以 JSON schema 限制輸出格式。未通過檢查的內容應該剔除或標記，而不是直接呈現給使用者。

## 評估方式
自動化指標如 BLEU、ROUGE 只衡量文字重疊，無法反映臨床正確性。醫療報告生成應加入臨床正確性評估，例如關鍵發現的召回率與錯誤率，並由臨床醫師進行盲測評分。

## 本機部署與責任
在醫院內以本機模型（例如透過 Ollama）執行，可以避免病人影像與報告上傳到外部雲端服務。AI 產生的報告只能作為草稿，最終內容必須由醫師審閱與簽署（human-in-the-loop）。
