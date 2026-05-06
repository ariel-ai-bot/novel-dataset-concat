#!/usr/bin/env python3
"""
Novel Dataset Concatenator
自動合併目錄下所有子資料夾的 .jsonl 檔案，或單一本小說的 JSONL 資料集。

功能：
- 模式 1：掃描子資料夾（每本小說一個）→ 合併多本小說
- 模式 2：直接讀取資料夾內所有 JSONL → 單一本小說的合併
- 自動標記每個樣本的來源（資料夾名稱）
- 產出詳細統計報告（總樣本數、來源分佈、Category 分佈）
- 支援 HuggingFace datasets 格式，可直接用於 Unsloth 微調

用法：
    # 多本小說模式（掃描子資料夾）
    python concat_novel_datasets.py --input ./datasets --output combined.jsonl
    
    # 單一本小說模式（直接讀取 JSONL）
    python concat_novel_datasets.py --input ./novel_dataset --output combined.jsonl --flat
    
    # 包含統計報告
    python concat_novel_datasets.py --input ./datasets --output combined.jsonl --report report.txt
    
    # HuggingFace 格式輸出
    python concat_novel_datasets.py --input ./datasets --output ./hf_dataset --format hf
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime


def find_jsonl_files(input_dir: str, flat_mode: bool = False, exclude_files: list = None) -> dict[str, list[str]]:
    """
    找出所有 .jsonl 檔案，按來源分組。
    
    Args:
        input_dir: 輸入目錄路徑
        flat_mode: 平直模式（不掃描子資料夾，直接讀取所有 JSONL）
        exclude_files: 要排除的檔案名稱列表
    
    Returns:
        dict: {來源名稱: [jsonl 檔案路徑列表]}
    """
    if exclude_files is None:
        exclude_files = []
    
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"❌ 找不到目錄: {input_dir}")
        sys.exit(1)
    
    result = {}
    
    if flat_mode:
        # 平直模式：直接讀取資料夾內所有 .jsonl 檔案
        jsonl_files = sorted(input_path.glob("*.jsonl"))
        for file_path in jsonl_files:
            if file_path.name not in exclude_files:
                result[file_path.name] = [str(file_path)]
    else:
        # 預設模式：掃描子資料夾
        found_any = False
        for subdir in sorted(input_path.iterdir()):
            if subdir.is_dir():
                jsonl_files = sorted(subdir.glob("*.jsonl"))
                if jsonl_files:
                    result[subdir.name] = [str(f) for f in jsonl_files if f.name not in exclude_files]
                    found_any = True
        
        # 如果沒有子資料夾但有 JSONL，自動切換到平直模式
        if not found_any:
            jsonl_files = sorted(input_path.glob("*.jsonl"))
            for file_path in jsonl_files:
                if file_path.name not in exclude_files:
                    result[file_path.name] = [str(file_path)]
            
            if not result:
                print(f"❌ 在 {input_dir} 中找不到任何 .jsonl 檔案或包含 .jsonl 的子資料夾")
                sys.exit(1)
    
    return result


def load_jsonl(file_path: str) -> list[dict]:
    """從 JSONL 檔案載入資料。"""
    samples = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    sample = json.loads(line)
                    samples.append(sample)
                except json.JSONDecodeError as e:
                    print(f"  ⚠️  跳過 {file_path}:{line_num} - {e}")
    except Exception as e:
        print(f"  ❌ 讀取失敗 {file_path}: {e}")
    return samples


def concat_datasets(input_dir: str, flat_mode: bool = False, exclude_files: list = None) -> tuple[list[dict], dict]:
    """
    合併所有 JSONL 檔案。
    
    Returns:
        (samples, stats): 合併後的樣本列表和統計資訊
    """
    source_files = find_jsonl_files(input_dir, flat_mode, exclude_files)
    
    all_samples = []
    stats = {
        'sources': {},
        'categories': Counter(),
        'total': 0,
    }
    
    print(f"📂 找到 {len(source_files)} 個來源:")
    
    for source_name, files in source_files.items():
        print(f"\n  📖 {source_name} ({len(files)} 個檔案)")
        source_samples = 0
        
        for file_path in files:
            samples = load_jsonl(file_path)
            source_samples += len(samples)
            
            for sample in samples:
                sample['_source'] = source_name  # 標記來源
                all_samples.append(sample)
                
                # 統計 category
                cat = sample.get('category', sample.get('type', 'unknown'))
                stats['categories'][cat] += 1
        
        stats['sources'][source_name] = source_samples
        stats['total'] += source_samples
        print(f"    ✅ 載入 {source_samples} 個樣本")
    
    return all_samples, stats


def save_jsonl(samples: list[dict], output_path: str) -> None:
    """將樣本保存為 JSONL 檔案。"""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in samples:
            line = json.dumps(sample, ensure_ascii=False)
            f.write(line + '\n')
    
    print(f"\n💾 已保存 {len(samples):,} 個樣本到: {output_path}")


def save_stats(stats: dict, output_path: str) -> None:
    """保存統計報告。"""
    report = []
    report.append("=" * 60)
    report.append("  Novel Dataset Concatenation Report")
    report.append("=" * 60)
    report.append(f"  時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"  總樣本數: {stats['total']:,}")
    report.append("")
    report.append("  各來源樣本數:")
    report.append("-" * 40)
    
    for source, count in sorted(stats['sources'].items(), key=lambda x: -x[1]):
        report.append(f"    📖 {source}: {count:,} 個樣本")
    
    report.append("")
    report.append("  Category 分佈:")
    report.append("-" * 40)
    
    for cat, count in stats['categories'].most_common():
        report.append(f"    📂 {cat}: {count:,} ({count/stats['total']*100:.1f}%)")
    
    report.append("")
    report.append("=" * 60)
    
    report_text = '\n'.join(report)
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"\n📊 統計報告已保存到: {output_path}")
    print(f"\n{report_text}")


def format_hf_datasets(samples: list[dict], output_dir: str) -> str:
    """
    將樣本格式化成 HuggingFace datasets 可用的格式。
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存為 JSONL（HF 可直接讀取）
    jsonl_path = os.path.join(output_dir, "dataset.jsonl")
    save_jsonl(samples, jsonl_path)
    
    # 建立 dataset_info.json（供 Axolotl 使用）
    info_path = os.path.join(output_dir, "dataset_info.json")
    dataset_info = {
        "dataset_jsonl": {
            "file_name": "dataset.jsonl",
            "columns": {
                "text": "text",
            }
        }
    }
    
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(dataset_info, f, ensure_ascii=False, indent=2)
    
    # 建立 README
    readme_path = os.path.join(output_dir, "README.md")
    readme = f"""# Combined Novel Dataset

自動合併的小說資料集

- 總樣本數: {len(samples):,}
- 建立時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 來源數: {len(samples)} 個來源

## 使用方法

### HuggingFace datasets
```python
from datasets import load_dataset
dataset = load_dataset("json", data_files="dataset.jsonl", split="train")
```

### Axolotl
```yaml
datasets:
  - path: dataset.jsonl
    ds_type: json
```

### Unsloth
```python
from datasets import load_dataset
dataset = load_dataset("json", data_files="dataset.jsonl", split="train")
```
"""
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print(f"\n📦 HuggingFace 格式已保存到: {output_dir}")
    return output_dir


def main():
    parser = argparse.ArgumentParser(
        description="自動合併 .jsonl 檔案為統一訓練集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 多本小說模式（預設，掃描子資料夾）
  python concat_novel_datasets.py --input ./datasets --output combined.jsonl
  
  # 單一本小說模式（直接讀取 JSONL）
  python concat_novel_datasets.py --input ./novel_dataset --output combined.jsonl --flat
  
  # 包含統計報告
  python concat_novel_datasets.py --input ./datasets --output combined.jsonl --report report.txt
  
  # HuggingFace 格式輸出
  python concat_novel_datasets.py --input ./datasets --output ./hf_dataset --format hf
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='輸入目錄路徑（子資料夾或包含 JSONL 的目錄）'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='輸出 JSONL 檔案路徑或目錄（--format hf 時為目錄）'
    )
    parser.add_argument(
        '--report', '-r',
        help='統計報告輸出路徑（預設與 output 同目錄）'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['jsonl', 'hf'],
        default='jsonl',
        help='輸出格式（預設: jsonl）'
    )
    parser.add_argument(
        '--flat',
        action='store_true',
        help='平直模式：直接讀取目錄內所有 .jsonl，不掃描子資料夾'
    )
    parser.add_argument(
        '--exclude', '-e',
        nargs='*',
        default=['dataset_combined.jsonl'],
        help='排除的檔案名稱（預設排除 dataset_combined.jsonl 避免重複）'
    )
    
    args = parser.parse_args()
    
    print("🚀 Novel Dataset Concatenator")
    print("=" * 40)
    print(f"📂 輸入目錄: {args.input}")
    print(f"📁 輸出: {args.output}")
    print(f"📋 模式: {'平直（單一本小說）' if args.flat else '子資料夾（多本小說）'}")
    if args.exclude:
        print(f"🚫 排除檔案: {', '.join(args.exclude)}")
    print()
    
    # 合併資料集
    samples, stats = concat_datasets(args.input, args.flat, exclude_files=args.exclude)
    
    if not samples:
        print("❌ 沒有找到任何樣本")
        sys.exit(1)
    
    # 輸出
    if args.format == 'hf':
        format_hf_datasets(samples, args.output)
    else:
        save_jsonl(samples, args.output)
    
    # 統計報告
    report_path = args.report or os.path.join(
        os.path.dirname(args.output) or '.', 
        'dataset_report.txt'
    )
    save_stats(stats, report_path)
    
    print(f"\n✨ 完成！共處理 {stats['total']:,} 個樣本")


if __name__ == '__main__':
    main()
