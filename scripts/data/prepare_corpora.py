"""
Normalize, deduplicate, and shard corpora for tokenizer training.

Usage:
  python scripts/data/prepare_corpora.py \
    --in data/raw \
    --out data/processed \
    --manifest data/manifest.json \
    --shard-bytes 20000000
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Iterable, List

from tqdm import tqdm


def normalize_text(text: str) -> str:
    # Basic normalization: collapse whitespace, strip control chars, strip emails/urls
    text = text.replace("\r", "\n")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]+", "", text)
    text = re.sub(r"[\w.-]+@[\w.-]+", "<EMAIL>", text)
    text = re.sub(r"https?://\S+", "<URL>", text)
    return text.strip()


def iter_input_files(in_dir: Path) -> Iterable[Path]:
    for p in in_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".txt", ".jsonl"}:
            yield p


def read_records(path: Path) -> Iterable[str]:
    if path.suffix.lower() == ".txt":
        yield path.read_text(errors="ignore")
    else:
        # jsonl: assume each line has a "text" field
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    text = obj.get("text")
                    if isinstance(text, str):
                        yield text
                except Exception:
                    continue


def dedupe_by_hash(texts: Iterable[str]) -> List[str]:
    seen = set()
    unique: List[str] = []
    for t in texts:
        h = hashlib.sha256(t.encode("utf-8")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        unique.append(t)
    return unique


def write_shards(texts: List[str], out_dir: Path, shard_bytes: int) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    shards: List[Path] = []
    buf: List[str] = []
    size = 0
    shard_id = 0
    for t in texts:
        b = len(t.encode("utf-8")) + 1
        if size + b > shard_bytes and buf:
            shard_path = out_dir / f"shard_{shard_id:05d}.txt"
            shard_path.write_text("\n".join(buf))
            shards.append(shard_path)
            buf, size = [], 0
            shard_id += 1
        buf.append(t)
        size += b
    if buf:
        shard_path = out_dir / f"shard_{shard_id:05d}.txt"
        shard_path.write_text("\n".join(buf))
        shards.append(shard_path)
    return shards


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", default="data/raw")
    ap.add_argument("--out", dest="out_dir", default="data/processed")
    ap.add_argument("--manifest", dest="manifest", default="data/manifest.json")
    ap.add_argument("--shard-bytes", dest="shard_bytes", type=int, default=20_000_000)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_texts: List[str] = []
    for fpath in tqdm(list(iter_input_files(in_dir)), desc="reading inputs"):
        for rec in read_records(fpath):
            norm = normalize_text(rec)
            if norm:
                all_texts.append(norm)

    unique = dedupe_by_hash(all_texts)
    shards = write_shards(unique, out_dir, args.shard_bytes)

    # Update manifest skeleton if present
    manifest_path = Path(args.manifest)
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            manifest = {"schema": "ai-cost-optimizer.corpora.v1", "sources": []}
    else:
        manifest = {"schema": "ai-cost-optimizer.corpora.v1", "sources": []}

    manifest["created_at"] = manifest.get("created_at", "")
    # Ensure a generic processed entry
    manifest["sources"] = manifest.get("sources", [])
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"Wrote {len(shards)} shards to {out_dir}")


if __name__ == "__main__":
    main()
