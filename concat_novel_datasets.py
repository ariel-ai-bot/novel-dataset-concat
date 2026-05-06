#!/usr/bin/env python3
"""合併多個 JSONL 訓練集為單一檔案，支援小說數據集批量處理。"""
import argparse
import json
import os
import shutil
from collections import Counter
from pathlib import Path

from datasets import load_dataset


def find_jsonl_files(input_path: str, exclude_files: set = None, flat_mode: bool = False) -> dict:
    """Find all .jsonl files in input directory.
    
    Returns dict: {source_name: [file_paths]}
    """
    if exclude_files is None:
        exclude_files = set()

    input_dir = Path(input_path)
    result = {}

    if flat_mode or not any(p.is_dir() for p in input_dir.iterdir()):
        # 平直模式：同層所有 .jsonl
        for f in sorted(input_dir.iterdir()):
            if f.is_file() and f.suffix == ".jsonl" and f.name not in exclude_files:
                source = f.stem
                if source not in result:
                    result[source] = []
                result[source].append(str(f))
    else:
        # 多本小說模式：每個子資料夾一組
        for sub in sorted(input_dir.iterdir()):
            if sub.is_dir():
                source_name = sub.name
                jsonls = []
                for f in sorted(sub.iterdir()):
                    if f.is_file() and f.suffix == ".jsonl" and f.name not in exclude_files:
                        jsonls.append(str(f))
                if jsonls:
                    result[source_name] = jsonls

    return result


def concat_datasets(source_files: dict, output_dir: str, output_hf: bool = False,
                    exclude_files: set = None) -> dict:
    """Concatenate all JSONL files and write combined output."""
    if exclude_files is None:
        exclude_files = set()

    os.makedirs(output_dir, exist_ok=True)

    all_records = []
    category_counts = Counter()
    source_counts = Counter()

    for source_name, file_paths in source_files.items():
        source_total = 0
        for fp in file_paths:
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        all_records.append(record)
                        category_counts[record.get("category", "unknown")] += 1
                        source_total += 1
                    except json.JSONDecodeError as e:
                        print(f"⚠️  跳過無效 JSON ({fp}): {e}")
        source_counts[source_name] = source_total
        print(f"  📖 {source_name}: {source_total} 筆")

    # 寫入合併後 JSONL
    combined_path = os.path.join(output_dir, "dataset_combined.jsonl")
    with open(combined_path, "w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\n💾 已寫入 {combined_path} ({len(all_records)} 筆)")

    # 寫入 HuggingFace datasets 格式
    if output_hf:
        from datasets import Dataset
        dataset = Dataset.from_list(all_records)
        hf_dir = os.path.join(output_dir, "hf_dataset")
        dataset.save_to_disk(hf_dir)
        print(f"💾 HuggingFace datasets: {hf_dir}")

    # 寫入統計報告
    report_lines = [
        "=" * 50,
        "  合併統計報告",
        "=" * 50,
        f"  總樣本數: {len(all_records)} 筆",
        "",
        "  各來源計數:",
    ]
    for source, count in sorted(source_counts.items()):
        report_lines.append(f"    {source}: {count} 筆")
    report_lines.extend(["", "  Category 分佈:"])
    for cat, count in sorted(category_counts.items()):
        report_lines.append(f"    {cat}: {count} 筆")
    report_lines.append("=" * 50)

    report_text = "\n".join(report_lines)
    print(f"\n{report_text}")
    print(f"📊 報告已輸出到 {combined_path.replace('.jsonl', '_report.txt')}")

    report_path = combined_path.replace(".jsonl", "_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text + "\n")

    return {
        "total": len(all_records),
        "sources": dict(source_counts),
        "categories": dict(category_counts),
    }


def main():
    parser = argparse.ArgumentParser(description="合併多個 JSONL 訓練集為單一檔案")
    parser.add_argument("-i", "--input", required=True, help="輸入目錄路徑")
    parser.add_argument("-o", "--output", default=None, help="輸出目錄路徑")
    parser.add_argument("--flat", action="store_true", help="強制平直模式（同層 JSONL）")
    parser.add_argument("-e", "--exclude", nargs="*", default=None,
                        help="要排除的檔案名稱（預設排除 dataset_combined.jsonl）")
    parser.add_argument("--hf", action="store_true", help="同時輸出 HuggingFace datasets 格式")
    parser.add_argument("-r", "--report", default=None, help="統計報告輸出位置")
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input)
    if not os.path.isdir(input_dir):
        print(f"❌ 輸入目錄不存在: {input_dir}")
        return

    # 預設排除
    default_exclude = {"dataset_combined.jsonl"}
    if args.exclude is not None:
        exclude_files = set(args.exclude) if args.exclude else set()
    else:
        exclude_files = default_exclude

    # 輸出目錄
    if args.output:
        output_dir = os.path.abspath(args.output)
    else:
        output_dir = os.path.join(input_dir, "combined")

    print(f"📁 輸入: {input_dir}")
    print(f"📁 輸出: {output_dir}")
    print(f"🔍 排除: {exclude_files}")
    print(f"📋 模式: {'平直模式' if args.flat else '自動偵測'}\n")

    # 找出 JSONL 檔案
    source_files = find_jsonl_files(input_dir, exclude_files, args.flat)
    if not source_files:
        print("⚠️  找不到任何 JSONL 檔案")
        return

    print(f"📚 找到 {len(source_files)} 個來源:\n")
    for name, paths in source_files.items():
        print(f"  📖 {name}: {len(paths)} 個檔案")
    print()

    # 合併
    result = concat_datasets(source_files, output_dir, args.hf, exclude_files)

    print(f"\n✅ 完成！總計 {result['total']} 筆樣本")


if __name__ == "__main__":
    main()
