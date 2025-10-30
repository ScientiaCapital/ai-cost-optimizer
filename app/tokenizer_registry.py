import threading
from typing import Optional, Tuple

_lock = threading.Lock()
_cache = {}


def _load_tokenizer(repo_id: str):
    try:
        from transformers import AutoTokenizer  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Tokenizers unavailable: install transformers (and sentencepiece if needed)"
        ) from e

    # Prefer slow tokenizer to avoid rust wheels
    tok = AutoTokenizer.from_pretrained(repo_id, use_fast=False)
    return tok


def get_tokenizer(repo_id: str):
    with _lock:
        if repo_id in _cache:
            return _cache[repo_id]
        tok = _load_tokenizer(repo_id)
        _cache[repo_id] = tok
        return tok


def estimate_tokenization_metrics(text: str, tokenizer_id: Optional[str]) -> Optional[Tuple[int, float, float]]:
    """
    Estimate token counts using the provided tokenizer repo id.

    Returns (num_tokens, bytes_per_token, tokens_per_byte) or None if no tokenizer_id.
    """
    if not tokenizer_id:
        return None
    tok = get_tokenizer(tokenizer_id)
    enc = tok(text, add_special_tokens=False, return_attention_mask=False, return_token_type_ids=False)
    ids = enc.get("input_ids", [])
    total_tokens = len(ids)
    total_bytes = len(text.encode("utf-8")) if text else 0
    if total_tokens == 0 or total_bytes == 0:
        return (total_tokens, 0.0, 0.0)
    bpt = total_bytes / total_tokens
    tpb = total_tokens / total_bytes
    return (total_tokens, bpt, tpb)


