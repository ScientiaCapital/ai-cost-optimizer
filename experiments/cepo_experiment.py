"""
CePO experiment runner using OptiLLM with Cerebras Inference.

Prereqs:
  pip install --upgrade cerebras_cloud_sdk optillm
  export CEREBRAS_API_KEY=...  (or place in .env at project root)

Run:
  python experiments/cepo_experiment.py --question "Solve: If 2x+3=11, what is x?"
"""
from __future__ import annotations

import argparse
import os
from typing import Optional

from dotenv import load_dotenv


def run_cepo(question: str, model: str = "llama3.3-70b", cepo_print_output: bool = False) -> None:
    # Lazy import to avoid importing when not needed
    try:
        from optillm import cli as opti_cli
    except Exception as e:
        raise RuntimeError(
            "optillm is not installed. Run: pip install --upgrade optillm"
        ) from e

    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        raise RuntimeError("CEREBRAS_API_KEY is not set in environment")

    # Build CLI args for OptiLLM
    # Equivalent to:
    # optillm --base-url https://api.cerebras.ai --approach cepo --model llama3.3-70b --cepo_print_output true
    args = [
        "--base-url",
        "https://api.cerebras.ai",
        "--approach",
        "cepo",
        "--model",
        model,
        "--prompt",
        question,
    ]
    if cepo_print_output:
        args += ["--cepo_print_output", "true"]

    # OptiLLM parses env var CEREBRAS_API_KEY internally
    opti_cli.main(args)


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run a CePO reasoning experiment via Cerebras")
    parser.add_argument("--question", required=True, help="Problem to solve")
    parser.add_argument(
        "--model",
        default="llama3.3-70b",
        help="Cerebras model (CePO currently demonstrated with llama3.3-70b)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print intermediate CePO states in OptiLLM logs",
    )
    args = parser.parse_args()

    run_cepo(question=args.question, model=args.model, cepo_print_output=args.verbose)


if __name__ == "__main__":
    main()


