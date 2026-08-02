"""Two-stage recommend: matrix factorization generates candidates, a second
ranking pass blends the predicted rating with item popularity.

Real deep-learning rankers (a small neural net taking [user_vec, item_vec,
context] -> relevance) need a training framework — PyTorch is blocked on
this host by Smart App Control (see app/modules/rag/models.py). This linear
blend is the honest, dependency-free stand-in for that ranking stage; the
candidate generation above it (matrix factorization) is unaffected and real.
"""

from app.modules.recommendations.mf import MatrixFactorizationModel
from app.modules.recommendations.schemas import RecommendationItem

RATING_WEIGHT = 0.8
POPULARITY_WEIGHT = 0.2


def recommend_for_user(
    model: MatrixFactorizationModel, user_id: str, top_k: int = 10
) -> list[RecommendationItem]:
    candidates = model.candidates_for_user(user_id)
    scored = []
    for item_id in candidates:
        predicted = model.predict(user_id, item_id)
        popularity = model.item_popularity.get(item_id, 0.0)
        final = RATING_WEIGHT * predicted + POPULARITY_WEIGHT * popularity * 5.0
        scored.append(
            RecommendationItem(
                item_id=item_id,
                predicted_rating=round(predicted, 4),
                popularity=round(popularity, 4),
                final_score=round(final, 4),
            )
        )
    scored.sort(key=lambda r: r.final_score, reverse=True)
    return scored[:top_k]
