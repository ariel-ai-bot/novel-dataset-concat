# 📚 Novel Dataset Concatenator

自動合併目錄下所有子資料夾的 `.jsonl` 檔案，或單一本小說的 JSONL 資料集。

專為小說微調設計，可處理多本小說的 SFT JSONL 資料。

## ✨ 功能

- 📂 自動掃描子資料夾（每本小說一個資料夾）
- 🔄 直接讀取單一本小說的 JSONL 檔案（`--flat` 模式）
- 🤖 自動偵測模式（有子資料夾自動用子資料夾模式，否則用平直模式）
- 🚫 預設排除 `dataset_combined.jsonl` 避免重複
- 📊 產出詳細統計報告（每本小說的樣本數、Category 分佈）
- 💾 輸出標準 JSONL 格式
- 🤗 支援 HuggingFace datasets 格式輸出
- 📦 可與 Unsloth、Axolotl 無縫配合

## 📁 推薦目錄結構

### 多本小說模式（預設）

```
datasets/
├── novel_a/
│   ├── dialogue_learn.jsonl
│   ├── continuation.jsonl
│   └── narration_learn.jsonl
├── novel_b/
│   ├── dialogue_learn.jsonl
│   └── continuation.jsonl
└── general_sft/
    └── dataset.jsonl
```

### 單一本小說模式（`--flat`）

```
novel_dataset/
├── knowledge_inject.jsonl
├── dialogue_learn.jsonl
├── continuation.jsonl
├── narration_learn.jsonl
├── style_rewrite.jsonl
├── character_scene.jsonl
├── chapter_context.jsonl
└── dataset_combined.jsonl  ← 自動排除，避免重複
```

## 🚀 使用方法

### 基本用法（多本小說）

```bash
# 合併所有子資料夾的 .jsonl 檔案
python concat_novel_datasets.py \
  --input ./datasets \
  --output combined.jsonl
```

### 單一本小說模式

```bash
# 直接讀取資料夾內所有 .jsonl 檔案
python concat_novel_datasets.py \
  --input ./novel_dataset \
  --output combined.jsonl \
  --flat
```

### 自動偵測模式

```bash
# 腳本會自動偵測：
# - 如果有子資料夾包含 .jsonl → 使用子資料夾模式
# - 如果沒有子資料夾但有 .jsonl → 使用平直模式
python concat_novel_datasets.py \
  --input ./datasets \
  --output combined.jsonl
```

### 自訂排除檔案

```bash
# 排除特定檔案（預設排除 dataset_combined.jsonl）
python concat_novel_datasets.py \
  --input ./datasets \
  --output combined.jsonl \
  --exclude file1.jsonl file2.jsonl
```

### 包含統計報告

```bash
python concat_novel_datasets.py \
  --input ./datasets \
  --output combined.jsonl \
  --report report.txt
```

### HuggingFace 格式輸出

```bash
python concat_novel_datasets.py \
  --input ./datasets \
  --output ./hf_dataset \
  --format hf
```

## 🤗 與 Unsloth 配合使用

```python
from datasets import load_dataset

# 載入合併後的資料集
dataset = load_dataset("json", data_files="combined.jsonl", split="train")

# 或直接使用 HF 格式
dataset = load_dataset("./hf_dataset", split="train")
```

## 📊 統計報告範例

```
============================================================
  Novel Dataset Concatenation Report
============================================================
  時間: 2025-01-15 14:30:00
  總樣本數: 15,432

  各來源樣本數:
----------------------------------------
    📖 novel_a: 8,234 個樣本
    📖 novel_b: 5,128 個樣本
    📖 general_sft: 2,070 個樣本

  Category 分佈:
----------------------------------------
    📂 continuation: 9,876 (64.0%)
    📂 dialogue_learn: 3,456 (22.4%)
    📂 narration_learn: 1,234 (8.0%)
    📂 knowledge_inject: 866 (5.6%)
============================================================
```

## ⚙️ 參數說明

| 參數 | 簡寫 | 說明 | 預設值 |
|------|------|------|--------|
| `--input` | `-i` | 輸入目錄路徑（子資料夾或包含 JSONL 的目錄） | 必填 |
| `--output` | `-o` | 輸出檔案/目錄路徑 | 必填 |
| `--report` | `-r` | 統計報告輸出路徑 | 與 output 同目錄 |
| `--format` | `-f` | 輸出格式 (`jsonl` / `hf`) | `jsonl` |
| `--flat` | - | 平直模式（直接讀取所有 JSONL，不掃描子資料夾） | 自動偵測 |
| `--exclude` | `-e` | 排除的檔案名稱（預設排除 dataset_combined.jsonl） | `dataset_combined.jsonl` |

## 📝 依賴

- Python 3.10+
- 標準函式庫（無需額外安裝）

## 📄 License

MIT

## 👤 Author

Ariel - 為小說微調而生 🦥
