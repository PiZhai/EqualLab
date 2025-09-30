from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .equivalence import are_equivalent
from .structure import structure_similarity


@dataclass
class SimilarityResult:
    equivalent: bool
    score: float
    detail: dict


def similarity(expr1: sp.Expr, expr2: sp.Expr, w_equiv: float = 0.7, assumptions: dict | None = None) -> SimilarityResult:
    eq = are_equivalent(expr1, expr2, assumptions=assumptions)
    struct = structure_similarity(sp.simplify(expr1), sp.simplify(expr2))

    if eq.is_equivalent:
        # 等价直接返回满分
        return SimilarityResult(True, 1.0, {
            "equivalence": eq.__dict__,
            "structure": struct,
            "weights": {"equiv": w_equiv, "struct": 1 - w_equiv},
        })

    eq_score = 0.0
    score = w_equiv * eq_score + (1 - w_equiv) * struct
    return SimilarityResult(
        equivalent=eq.is_equivalent,
        score=float(max(0.0, min(1.0, score))),
        detail={
            "equivalence": eq.__dict__,
            "structure": struct,
            "weights": {"equiv": w_equiv, "struct": 1 - w_equiv},
        },
    )


