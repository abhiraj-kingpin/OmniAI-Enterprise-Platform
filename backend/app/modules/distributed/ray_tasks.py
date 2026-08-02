"""Real Ray usage — a local single-node cluster (`ray.init()` with no
address needs no separate Ray head process), genuinely parallelizing work
across worker processes. Unlike PyTorch/numba, Ray's compiled core
(`_raylet`) isn't blocked by this host's Smart App Control policy.

Single-node here, but the code is unchanged if pointed at a real cluster —
swap `ray.init()` for `ray.init(address="ray://head-node:10001")` and the
same @ray.remote functions distribute across it. GPU Scheduling: give a
remote function `@ray.remote(num_gpus=1)` and Ray's scheduler places it only
on a worker with a free GPU — same API, we just have none to allocate here.
"""

import time
from functools import lru_cache

import ray


@lru_cache(maxsize=1)
def ensure_ray() -> None:
    if not ray.is_initialized():
        ray.init(num_cpus=4, ignore_reinit_error=True, logging_level="warning")


@ray.remote
def _text_stats(text: str) -> dict:
    words = text.split()
    return {
        "text_preview": text[:60],
        "word_count": len(words),
        "char_count": len(text),
        "avg_word_length": round(sum(len(w) for w in words) / len(words), 2) if words else 0,
    }


def parallel_map(items: list[str]) -> tuple[list[dict], float, int]:
    ensure_ray()
    start = time.perf_counter()
    futures = [_text_stats.remote(item) for item in items]
    results = ray.get(futures)
    elapsed = time.perf_counter() - start
    return results, elapsed, int(ray.available_resources().get("CPU", 0))
