"""Matrix factorization collaborative filtering (Funk-SVD / SGD), hand-rolled
in numpy rather than pulled from a library — deliberately: after PyTorch got
blocked by this host's Smart App Control policy (see app/modules/rag/models.py),
this module sticks to numpy/pandas, which are already proven to work, instead
of risking another unfamiliar native dependency.
"""

import numpy as np
import pandas as pd


class MatrixFactorizationModel:
    def __init__(self, factors: int = 20) -> None:
        self.factors = factors
        self.user_ids: list[str] = []
        self.item_ids: list[str] = []
        self._user_idx: dict[str, int] = {}
        self._item_idx: dict[str, int] = {}
        self.user_factors: np.ndarray = np.zeros((0, factors))
        self.item_factors: np.ndarray = np.zeros((0, factors))
        self.global_mean: float = 0.0
        self.item_popularity: dict[str, float] = {}
        self.user_seen: dict[str, set[str]] = {}

    def fit(
        self,
        df: pd.DataFrame,
        user_col: str = "user_id",
        item_col: str = "item_id",
        rating_col: str = "rating",
        epochs: int = 30,
        lr: float = 0.01,
        reg: float = 0.02,
        seed: int = 42,
    ) -> float:
        self.user_ids = sorted(df[user_col].astype(str).unique())
        self.item_ids = sorted(df[item_col].astype(str).unique())
        self._user_idx = {u: i for i, u in enumerate(self.user_ids)}
        self._item_idx = {i: idx for idx, i in enumerate(self.item_ids)}

        n_users, n_items = len(self.user_ids), len(self.item_ids)
        rng = np.random.default_rng(seed)
        self.user_factors = rng.normal(0, 0.1, (n_users, self.factors))
        self.item_factors = rng.normal(0, 0.1, (n_items, self.factors))

        ratings = df[rating_col].astype(float).values
        self.global_mean = float(ratings.mean())

        u_indices = df[user_col].astype(str).map(self._user_idx).values
        i_indices = df[item_col].astype(str).map(self._item_idx).values

        n = len(df)
        rmse = 0.0
        for _epoch in range(epochs):
            order = rng.permutation(n)
            sq_err_sum = 0.0
            for k in order:
                u, i, r = u_indices[k], i_indices[k], ratings[k]
                pred = self.global_mean + self.user_factors[u] @ self.item_factors[i]
                err = r - pred
                sq_err_sum += err**2

                u_vec = self.user_factors[u].copy()
                self.user_factors[u] += lr * (err * self.item_factors[i] - reg * u_vec)
                self.item_factors[i] += lr * (err * u_vec - reg * self.item_factors[i])
            rmse = float(np.sqrt(sq_err_sum / n))

        counts = df[item_col].astype(str).value_counts()
        max_count = counts.max() if len(counts) else 1
        self.item_popularity = {item: count / max_count for item, count in counts.items()}

        self.user_seen = {
            u: set(items) for u, items in df.groupby(df[user_col].astype(str))[item_col].apply(
                lambda s: s.astype(str).tolist()
            ).items()
        }

        return rmse

    def has_user(self, user_id: str) -> bool:
        return user_id in self._user_idx

    def has_item(self, item_id: str) -> bool:
        return item_id in self._item_idx

    def predict(self, user_id: str, item_id: str) -> float:
        u = self._user_idx.get(user_id)
        i = self._item_idx.get(item_id)
        if u is None or i is None:
            return self.global_mean
        return float(self.global_mean + self.user_factors[u] @ self.item_factors[i])

    def candidates_for_user(self, user_id: str) -> list[str]:
        seen = self.user_seen.get(user_id, set())
        return [item for item in self.item_ids if item not in seen]

    def similar_items(self, item_id: str, top_k: int = 10) -> list[tuple[str, float]]:
        idx = self._item_idx.get(item_id)
        if idx is None:
            return []
        target = self.item_factors[idx]
        norms = np.linalg.norm(self.item_factors, axis=1) * np.linalg.norm(target)
        norms[norms == 0] = 1e-9
        sims = (self.item_factors @ target) / norms
        order = np.argsort(-sims)
        results = [
            (self.item_ids[i], float(sims[i])) for i in order if self.item_ids[i] != item_id
        ]
        return results[:top_k]
