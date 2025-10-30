"""
Train tokenizer(s): BPE baseline via HuggingFace tokenizers, and optionally SuperBPE if installed.

Usage (baseline BPE):
  python scripts/tokenizer/train_superbpe.py --data data/processed --out artifacts/tokenizers/bpe-100k --vocab 100000 --algo bpe

Usage (SuperBPE, requires `superbpe` package):
  python scripts/tokenizer/train_superbpe.py --data data/processed --out artifacts/tokenizers/superbpe-200k --vocab 200000 --algo superbpe
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

from tqdm import tqdm


def iter_corpus_files(data_dir: Path) -> Iterable[Path]:
    for p in data_dir.rglob("shard_*.txt"):
        if p.is_file():
            yield p


def train_bpe(data_dir: Path, out_dir: Path, vocab_size: int) -> None:
    from tokenizers import Tokenizer
    from tokenizers.models import BPE
    from tokenizers.trainers import BpeTrainer
    from tokenizers.pre_tokenizers import Whitespace

    out_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = Tokenizer(BPE(unk_token="<unk>"))
    tokenizer.pre_tokenizer = Whitespace()

    trainer = BpeTrainer(
        vocab_size=vocab_size,
        special_tokens=["<unk>", "<pad>", "<s>", "</s>", "<mask>"]
    )

    files = [str(p) for p in iter_corpus_files(data_dir)]
    tokenizer.train(files, trainer)

    (out_dir / "tokenizer.json").write_text(tokenizer.to_str())
    print(f"Saved BPE tokenizer to {out_dir}")


def train_superbpe(data_dir: Path, out_dir: Path, vocab_size: int) -> None:
    try:
        import superbpe  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "superbpe package not installed. See https://github.com/PythonNut/superbpe"
        ) from e

    out_dir.mkdir(parents=True, exist_ok=True)

    # This is a placeholder API; refer to the superbpe repo for the exact CLI/API.
    # Example pseudocode-like usage:
    # superbpe.train(
    #   input_files=[str(p) for p in iter_corpus_files(data_dir)],
    #   vocab_size=vocab_size,
    #   output_dir=str(out_dir),
    #   pretokenization_curriculum=True,
    # )
    raise NotImplementedError("Integrate superbpe training per upstream API.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/processed")
    ap.add_argument("--out", required=True)
    ap.add_argument("--vocab", type=int, default=100_000)
    ap.add_argument("--algo", choices=["bpe", "superbpe"], default="bpe")
    args = ap.parse_args()

    data_dir = Path(args.data)
    out_dir = Path(args.out)

    if args.algo == "bpe":
        train_bpe(data_dir, out_dir, args.vocab)
    else:
        train_superbpe(data_dir, out_dir, args.vocab)


if __name__ == "__main__":
    main()
