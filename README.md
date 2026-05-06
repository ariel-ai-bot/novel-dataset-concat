# novel-dataset-concat

自動合併多個 JSONL 訓練集為單一檔案，支援小說數據集的批量處理。

## 功能

- 📁 **雙模式掃描**：自動偵測子資料夾結構（多本小說模式）或平直資料夾（單本小說模式）
- 🔍 **自動排除**：預設排除 `dataset_combined.jsonl`，避免資料重複
- 📊 **統計報告**：自動產生總樣本數、各來源計數與 Category 分佈
- 💾 **雙格式輸出**：標準 JSONL + HuggingFace `datasets` 格式

## 快速開始

```bash
# 1. 安裝依賴
pip install datasets

# 2. 合併單本小說（同層 JSONL）
python concat_novel_datasets.py --input /path/to/dataset

# 3. 合併多本小說（子資料夾結構）
python concat_novel_datasets.py --input /path/to/novels
```

## 命令列參數

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `--input, -i` | （必填） | 輸入目錄路徑 |
| `--output, -o` | `<input>/combined` | 輸出目錄 |
| `--flat` | 自動偵測 | 強制平直模式（同層 JSONL） |
| `--exclude, -e` | `dataset_combined.jsonl` | 要排除的檔案 |
| `--hf` | 關閉 | 同時輸出 HuggingFace datasets 格式 |
| `--report, -r` | 輸出目錄內 | 統計報告輸出位置 |

## 📌 預設排除檔案

`dataset_combined.jsonl`（`novel-dataset-builder` 的預設產出），避免資料重複。
如需強制包含，傳入 `-e` 清空預設排除：

```bash
python concat_novel_datasets.py --input /root/novel_dataset -e
```

---

## 📖 JSONL 格式說明

每個 `.jsonl` 檔案包含標準化的 JSON 物件，每行一筆。

### 欄位定義

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `category` | string | ✅ | 資料類別，對應檔案名稱 |
| `instruction` | string | ✅ | 系統提示 / 任務說明 |
| `context` | string | ❌ | 情境描述（可選） |
| `input` | string | ❌ | 使用者輸入 / 提問（可選，知識型類別留空） |
| `response` | string | ✅ | 角色 / 系統回覆 |

### `category` 類別對照

| 類別 | 對應檔案 | 用途 |
|------|----------|------|
| `knowledge_inject` | `knowledge_inject.jsonl` | 角色設定、世界觀 |
| `character` | `character.jsonl` | 角色互動對話 |
| `emotion` | `emotion.jsonl` | 情緒描寫 |
| `plot` | `plot.jsonl` | 劇情發展 |
| `worldview` | `worldview.jsonl` | 世界觀細節 |
| `skills` | `skills.jsonl` | 角色技能 |
| `summary` | `summary.jsonl` | 劇情摘要 |

### 範例：一個完整的 JSONL 紀錄

以下使用童話《小紅帽與森林公主》作為範例：

```json
{
  "category": "character",
  "instruction": "扮演童話中的角色，與使用者進行對話。",
  "context": "[角色：小紅帽]\n[情境：小紅帽在森林中遇到了大野狼]",
  "input": "你好呀！你是誰？我從來沒有在森林裡見過你。",
  "response": "（大野狼低下巨大的頭，金色的眼睛溫柔地看著小紅帽）\n\n「你好，小女孩。我是住在这片森林裡的野狼，你可以叫我狼先生。」"
}
```

```json
{
  "category": "knowledge_inject",
  "instruction": "請記住童話《小紅帽與森林公主》的角色設定。",
  "context": "【角色設定：小紅帽】\n暱稱：小紅帽、紅帽\n身份：女主角\n性別：女\n年齡：8歲\n性格：善良、勇敢、好奇、聽話、關心家人",
  "response": "已記住角色「小紅帽」的設定。"
}
```

```json
{
  "category": "plot",
  "instruction": "繼續這個故事的發展。",
  "context": "【第一章：小紅帽的旅程】\n\n奶奶生病了，媽媽給小紅帽準備了一籃子的食物，讓她送到森林深處的奶奶家。",
  "input": "接下來小紅帽在森林中遇到了什麼事？",
  "response": "小紅帽一边走一邊採著野花，花徑上開滿了五彩繽紛的花朵，美不勝收。"
}
```

> 💡 所有欄位都是 UTF-8 編碼的純文字。`context`、`input`、`response` 可使用 `\n` 進行換行。

---

## 📂 Sample 目錄

倉庫內附有 `sample_data/princess_story/` 作為完整範例，包含 7 個類別、共 15 筆樣本（童話故事《小紅帽與森林公主》）。
可直接執行 `python concat_novel_datasets.py --input sample_data/princess_story` 測試。

## 與 Unsloth 搭配使用

```python
from datasets import load_dataset

# 合併後的資料集可直接載入
dataset = load_dataset("json", data_files="/path/to/combined/dataset_combined.jsonl")
print(dataset)
# DatasetDict({
#     'train': Dataset({
#         'features': ['category', 'instruction', 'context', 'input', 'response'],
#         'num_rows': 1588
#     })
# })
```

## License

MIT License
