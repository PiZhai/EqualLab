from __future__ import annotations

from typing import Dict, List, Tuple
import re
import sympy as sp
from .formula import parse_formula
try:
    from chempy import balance_stoichiometry  # type: ignore
    _HAS_CHEMPY = True
except Exception:  # noqa: BLE001
    _HAS_CHEMPY = False


# 模块级：去除物种前置系数（整数/分数/小数）的正则
_COEF_PREFIX_PATTERN = r"^\s*(?:\d+(?:/\d+)?|\d*\.\d+)\s*"


def _split_reaction(s: str) -> Tuple[List[str], List[str]]:
    s = s.strip()
    # 支持更多箭头符号，包括双向与不同写法
    arrows = [
        '<=>', '<->', '⇌', '↔',  # reversible
        '=>', '→', '->', '⟶',    # forward
    ]
    arrow = None
    for a in arrows:
        if a in s:
            arrow = a
            break
    if arrow is None:
        # 默认尝试 '->'
        arrow = '->'
    left, right = [p.strip() for p in s.split(arrow, 1)]
    reag = [p.strip() for p in re.split(r"\+", left) if p.strip()]
    prod = [p.strip() for p in re.split(r"\+", right) if p.strip()]
    return reag, prod


def parse_reaction(s: str) -> Tuple[List[Tuple[int, Dict[str,int]]], List[Tuple[int, Dict[str,int]]]]:
    reag, prod = _split_reaction(s)
    def parse_term(term: str) -> Tuple[int, Dict[str,int]]:
        m = re.match(r"^(\d+)\s*(.*)$", term)
        coef = int(m.group(1)) if m else 1
        formula = m.group(2) if m else term
        return coef, parse_formula(formula)
    return [parse_term(t) for t in reag], [parse_term(t) for t in prod]


def balance_reaction_info(s: str) -> Tuple[List[int], List[int], List[str], List[str], str]:
    """返回 (reactant_coeffs, product_coeffs, reactants, products, method)
    method ∈ {"chempy", "sympy"}
    """
    reag, prod = _split_reaction(s)

    # Prefer chempy if available
    if _HAS_CHEMPY:
        def strip_coef(x: str) -> str:
            # 去除前置系数：整数/小数/分数，如 '2H2O'、'0.5 O2'、'1/2 O2'
            return re.sub(r"^\s*(?:\d+(?:/\d+)?|\d*\.\d+)\s*", "", x)
        reag_clean = [strip_coef(x) for x in reag]
        prod_clean = [strip_coef(x) for x in prod]
        try:
            R, P = balance_stoichiometry(set(reag_clean), set(prod_clean))
            reag_coef = [int(R.get(spc, 0)) for spc in reag_clean]
            prod_coef = [int(P.get(spc, 0)) for spc in prod_clean]
            # ensure nonzero
            if not any(c == 0 for c in reag_coef + prod_coef):
                return reag_coef, prod_coef, reag_clean, prod_clean, "chempy"
        except Exception:
            # fallback to sympy method
            pass

    # Fallback: SymPy nullspace method
    species = reag + prod
    # 去除前置系数：整数/分数/小数
    elems: List[str] = sorted({el for spc in species for el in parse_formula(re.sub(_COEF_PREFIX_PATTERN, "", spc)).keys()})

    rows = []
    for el in elems:
        row = []
        for spc in reag:
            f = parse_formula(re.sub(_COEF_PREFIX_PATTERN, "", spc))
            row.append(f.get(el, 0))
        for spc in prod:
            f = parse_formula(re.sub(_COEF_PREFIX_PATTERN, "", spc))
            row.append(-f.get(el, 0))
        rows.append(row)

    A = sp.Matrix(rows)
    null = A.nullspace()
    if not null:
        raise ValueError("no balancing solution")
    v = null[0]
    lcm = sp.ilcm(*[sp.denom(c) for c in v]) if any(sp.denom(c) != 1 for c in v) else 1
    coeffs = [int(sp.together(c*lcm)) for c in v]
    if all(c <= 0 for c in coeffs):
        coeffs = [-c for c in coeffs]

    reag_coef = coeffs[:len(reag)]
    prod_coef = coeffs[len(reag):]
    return reag_coef, prod_coef, reag, prod, "sympy"


def balance_reaction(s: str) -> Tuple[List[int], List[int], List[str], List[str]]:
    rc, pc, r, p, _method = balance_reaction_info(s)
    return rc, pc, r, p


def reactions_equivalent(a: str, b: str) -> bool:
    ar, ap, areag, aprod = balance_reaction(a)
    br, bp, breag, bprod = balance_reaction(b)
    # normalize to species dictionary with coefficients
    def norm_map(reag, coef_reag, prod, coef_prod):
        from collections import Counter
        def key(x):
            return re.sub(_COEF_PREFIX_PATTERN, "", x)
        m = Counter()
        for s, c in zip(reag, coef_reag): m[key(s)] += c
        for s, c in zip(prod, coef_prod): m[key(s)] -= c
        return dict(m)

    return norm_map(areag, ar, aprod, ap) == norm_map(breag, br, bprod, bp)


