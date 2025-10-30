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
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [str(p) for p in iter_corpus_files(data_dir)]
    if not files:
        raise RuntimeError("No shards found in data directory for SuperBPE training")

    # Try Python API first, then fallback to CLI if available
    try:
        import superbpe  # type: ignore
        # Heuristic API attempt; adjust when upstream API is confirmed
        if hasattr(superbpe, "train"):
            superbpe.train(
                input_files=files,
                vocab_size=vocab_size,
                output_dir=str(out_dir),
                pretokenization_curriculum=True,
            )
            return
    except Exception:
        pass

    # CLI fallback: try invoking a `superbpe` executable with common flags
    import shutil, subprocess
    cli = shutil.which("superbpe") or shutil.which("superbpe-cli") or shutil.which("python")
    if cli is None:
        raise RuntimeError("SuperBPE CLI not found. Install via: pip install git+https://github.com/PythonNut/superbpe")

    if cli.endswith("python"):
        cmd = [cli, "-m", "superbpe"]
    else:
        cmd = [cli]

    # Generic argument guess; update when upstream docs are finalized
    cmd += [
        "train",
        "--vocab-size", str(vocab_size),
        "--output", str(out_dir),
    ]
    # Append inputs (many CLIs accept multiple --input flags)
    for f in files:
        cmd += ["--input", f]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"SuperBPE CLI failed: {' '.join(cmd)}") from e


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
