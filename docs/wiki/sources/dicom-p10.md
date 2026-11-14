# DICOM Standard Part 10 - Media Storage and File Format (4TB Dataset Pipeline)

- id：`dicom-p10`
- 原始檔：`raw/04-dicom-part10.md`
- 引用：NEMA. DICOM PS3.10 Media Storage and File Format for Media Interchange. ; DICOM PS3.15 Annex E Attribute Confidentiality Profiles. ; DICOM PS3.3 X-Ray Angiographic Image IOD.
- 備註：本檔為專案整理稿（非標準原文），4TB 資料管線一節為專案工程備註。標籤編號請以 DICOM 標準最新版核對。

## 導讀（LLM 生成，已過數字檢查；檢核依據是下方原文段落）

DICOM Part 10 定義醫學影像的儲存格式，包含前導區、前綴、檔案中繼資訊與資料集。處理 4TB 血管造影資料時，需建立檔案清單、篩選 XA 影像並進行去識別化。

關鍵詞：DICOM PS3.10、File Meta Information、Media Storage SOP Class UID、Transfer Syntax UID、Number of Frames、Positioner Primary Angle、去識別化、pydicom

## 原文段落（檢索與交叉檢查的依據）

### `dicom-p10#1` DICOM Part 10 檔案結構

DICOM PS3.10 定義醫學影像在儲存媒體上的檔案格式。一個 Part 10 檔案依序包含：128 位元組的前導區（preamble）、4 個字元的前綴 "DICM"、檔案中繼資訊（File Meta Information，群組 0002），接著才是資料集（data set）本體。

### `dicom-p10#2` 檔案中繼資訊

檔案中繼資訊（群組 0002）固定以 Explicit VR Little Endian 編碼。重要欄位包括 Media Storage SOP Class UID（0002,0002）、Media Storage SOP Instance UID（0002,0003）與 Transfer Syntax UID（0002,0010）。Transfer Syntax 決定資料集與像素資料的編碼方式，例如 JPEG Lossless 的 UID 為 1.2.840.10008.1.2.4.70。

### `dicom-p10#3` 血管造影影像的關鍵標籤

X 光血管造影影像（XA）的 SOP Class UID 為 1.2.840.10008.5.1.4.1.1.12.1。造影通常是多影格（multi-frame）電影序列，相關欄位包括 Number of Frames（0028,0008）、Frame Time（0018,1063）與 Cine Rate（0018,0040）。C 臂角度記錄在 Positioner Primary Angle（0018,1510，LAO/RAO）與 Positioner Secondary Angle（0018,1511，頭位/足位），可用於自動判斷投影角度。

### `dicom-p10#4` 去識別化

資料離開醫院安全環境前，必須依 DICOM PS3.15 Annex E 的 Basic Application Level Confidentiality Profile 移除或替換可識別個人的欄位，例如病人姓名、病歷號、出生日期與機構名稱。也要檢查像素中是否燒錄（burned-in）文字，以及私有標籤（private tags）是否藏有個資。

### `dicom-p10#5` 4TB 資料管線（專案工程備註）

處理約 4TB 的血管造影 DICOM 資料時，建議流程為：（1）先建立檔案清單（manifest），記錄路徑、大小與雜湊值，作為可重跑的依據；（2）以 pydicom 的 stop_before_pixels 只讀標頭，快速建立中繼資料索引；（3）依 SOP Class UID 篩出 XA 影像；（4）去識別化後再解壓像素並轉存成分片（shard）檔；（5）每個步驟寫入完成紀錄，支援中斷後續跑（checkpoint/resume），並以多行程平行處理。
