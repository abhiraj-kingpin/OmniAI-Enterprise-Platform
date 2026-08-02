import pandas as pd

from app.modules.recommendations.mf import MatrixFactorizationModel


def _toy_interactions() -> pd.DataFrame:
    rows = []
    for u in range(10):
        for i in range(8):
            if (u + i) % 3 != 0:
                continue
            rating = 5.0 if (u % 2) == (i % 2) else 2.0
            rows.append((f"user_{u}", f"item_{i}", rating))
    return pd.DataFrame(rows, columns=["user_id", "item_id", "rating"])


def test_fit_reduces_error_and_populates_state():
    df = _toy_interactions()
    model = MatrixFactorizationModel(factors=5)
    rmse = model.fit(df, epochs=20)

    assert rmse >= 0
    assert len(model.user_ids) == df["user_id"].nunique()
    assert len(model.item_ids) == df["item_id"].nunique()
    assert model.has_user("user_0")
    assert not model.has_user("nonexistent_user")


def test_candidates_exclude_seen_items():
    df = _toy_interactions()
    model = MatrixFactorizationModel(factors=5)
    model.fit(df, epochs=5)

    seen = model.user_seen["user_0"]
    candidates = model.candidates_for_user("user_0")
    assert not (seen & set(candidates))


def test_similar_items_excludes_self_and_is_bounded():
    df = _toy_interactions()
    model = MatrixFactorizationModel(factors=5)
    model.fit(df, epochs=5)

    results = model.similar_items(model.item_ids[0], top_k=3)
    assert len(results) <= 3
    assert all(item_id != model.item_ids[0] for item_id, _ in results)


def test_predict_unknown_user_or_item_returns_global_mean():
    df = _toy_interactions()
    model = MatrixFactorizationModel(factors=5)
    model.fit(df, epochs=5)

    assert model.predict("nobody", "item_0") == model.global_mean
    assert model.predict("user_0", "nothing") == model.global_mean
