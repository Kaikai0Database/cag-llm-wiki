# Deep Learning-based Quantitative Coronary Angiography (QCA) for Stenosis Detection

- id：`dl-qca`
- 原始檔：`raw/03-dl-qca.md`
- 引用：綜合整理稿。參考：Popov M, et al. Dataset for automatic region-based coronary artery disease diagnostics using X-ray angiography images. Sci Data. 2024;11:20.（ARCADE 資料集，請核對）
- 備註：本檔為專案整理稿（方法學綜述，非單一論文原文）。數值與方法請以引用文獻核對。

## 導讀（LLM 生成，已過數字檢查；檢核依據是下方原文段落）

深度學習 QCA 管線包含五步，包括關鍵影格選擇、血管分割、分段標註、中心線萃取與狹窄偵測。評估指標包括 Dice 係數、IoU、敏感度、精確度與 F1，並與核心實驗室 QCA 進行比較。

關鍵詞：定量冠狀動脈造影、最小管腔直徑、參考血管直徑、深度學習 QCA 管線、物件偵測法、幾何量測法、Dice 係數、Bland-Altman 分析

## 原文段落（檢索與交叉檢查的依據）

### `dl-qca#1` 傳統 QCA 的原理

定量冠狀動脈造影（quantitative coronary angiography, QCA）以影像邊緣偵測找出血管內腔輪廓，計算最小管腔直徑（minimal lumen diameter, MLD）、參考血管直徑（reference vessel diameter, RVD）與病灶長度。直徑狹窄百分比的公式為 %DS = (1 − MLD / RVD) × 100。傳統 QCA 需要人工挑選影格、放置起訖點與校正，耗時且有操作者間差異。

### `dl-qca#2` 影像校正

QCA 需要把像素換算成毫米。常見做法是以已知直徑的導管作為校正物，或使用 DICOM 標頭中的 Imager Pixel Spacing（0018,1164）配合幾何放大率估算。校正誤差會直接影響 MLD 與 RVD 的絕對值，但對 %DS 的影響較小，因為 %DS 是比值。

### `dl-qca#3` 深度學習 QCA 管線

典型的深度學習 QCA 管線分為五步：（1）關鍵影格選擇，挑出顯影最好、通常接近舒張末期的影格；（2）血管分割，常用 U-Net 或 nnU-Net 類模型輸出血管遮罩；（3）分段標註，把血管遮罩分配到解剖分段；（4）中心線萃取與沿中心線的直徑剖面計算；（5）狹窄偵測與 %DS 估計。

### `dl-qca#4` 狹窄偵測的兩種做法

第一種是物件偵測法，直接以偵測框（bounding box）標出狹窄位置，例如 YOLO 或 Faster R-CNN 類模型。第二種是幾何量測法，從分割結果計算直徑剖面，再依 %DS 門檻判斷狹窄。幾何量測法可解釋性較高，能輸出與傳統 QCA 相同的 MLD、RVD 數值。

### `dl-qca#5` 評估指標

血管分割常用 Dice 係數與 IoU 評估。狹窄偵測常用敏感度、精確度與 F1。%DS 量測則與核心實驗室（core lab）QCA 比較，使用平均絕對誤差與 Bland-Altman 分析描述一致性。

### `dl-qca#6` 限制

血管造影是三維血管的二維投影，會有縮短效應（foreshortening）與血管重疊，單一角度可能低估或高估狹窄。建議整合多個投影角度的結果。模型在不同醫院、不同機型之間的泛化能力需要外部驗證。
