"""Synthetic interactions generator — user behavior modeling via a latent
preference model, so a demo dataset produces genuinely learnable structure
(not just noise) for the matrix factorization model to recover."""

import numpy as np
import pandas as pd


def generate_demo_interactions(
    n_users: int = 50,
    n_items: int = 40,
    n_factors: int = 5,
    density: float = 0.15,
    seed: int = 7,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    user_prefs = rng.normal(0, 1, (n_users, n_factors))
    item_attrs = rng.normal(0, 1, (n_items, n_factors))

    rows = []
    for u in range(n_users):
        n_interactions = max(3, int(n_items * density * rng.uniform(0.5, 1.5)))
        items = rng.choice(n_items, size=min(n_interactions, n_items), replace=False)
        for i in items:
            raw = user_prefs[u] @ item_attrs[i]
            rating = float(np.clip(round(3 + raw + rng.normal(0, 0.3)), 1, 5))
            rows.append((f"user_{u}", f"item_{i}", rating))

    return pd.DataFrame(rows, columns=["user_id", "item_id", "rating"])
