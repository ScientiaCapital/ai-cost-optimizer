"""
Evaluate tokenizer encoding efficiency on sample corpus.

Usage:
  python scripts/tokenizer/evaluate_tokenizer.py \
    --tokenizer artifacts/tokenizers/bpe-100k/tokenizer.json \
    --data data/processed
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from tqdm import tqdm


def iter_corpus_files(data_dir: Path) -> Iterable[Path]:
    for p in data_dir.rglob("shard_*.txt"):
        if p.is_file():
            yield p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--data", default="data/processed")
    args = ap.parse_args()

    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(args.tokenizer)

    total_bytes = 0
    total_tokens = 0

    data_dir = Path(args.data)
    for fpath in tqdm(list(iter_corpus_files(data_dir)), desc="evaluating"):
        text = fpath.read_text(errors="ignore")
        total_bytes += len(text.encode("utf-8"))
        enc = tok.encode(text)
        total_tokens += len(enc.ids)

    if total_tokens == 0 or total_bytes == 0:
        print("No data to evaluate.")
        return

    bytes_per_token = total_bytes / total_tokens
    tokens_per_byte = total_tokens / total_bytes

    print(f"bytes/token: {bytes_per_token:.4f}")
    print(f"tokens/byte: {tokens_per_byte:.6f}")


if __name__ == "__main__":
    main()
